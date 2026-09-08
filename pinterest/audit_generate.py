from __future__ import annotations

import csv, io, json, math, os, re, time, urllib.parse
from dataclasses import asdict, dataclass
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).parent
OUT = ROOT / "audit_output"
OUT.mkdir(exist_ok=True)
HEAD_SHA = os.environ["HEAD_SHA"]
REPO = os.environ.get("GITHUB_REPOSITORY", "nemchenik/test")
TEMPLATE = f"https://rawcdn.githack.com/{REPO}/{HEAD_SHA}/pinterest/card.html"
SITE = "https://catalog-plans.ru"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
S = requests.Session(); S.headers.update({"User-Agent": UA, "Referer": SITE + "/", "Accept-Language": "ru-RU,ru;q=.9"})
FILE_RE = re.compile(r"(?:https?:)?//catalog-plans\.ru/files/[^\"'<> )]+?\.(?:jpe?g|png|webp|avif)(?:\?[^\"'<> )]*)?", re.I)
REL_RE = re.compile(r"/files/[^\"'<> )]+?\.(?:jpe?g|png|webp|avif)(?:\?[^\"'<> )]*)?", re.I)

@dataclass
class Rec:
    project: str; page_url: str; page_title: str; h1: str
    area: str; dimensions: str; floors: str; material: str; style: str; feature: str
    image_url: str; image_width: int; image_height: int; white_ratio: float
    image_origin: str; image_context: str

def clean(v): return re.sub(r"\s+", " ", v or "").strip()

def get(url, timeout=35):
    err = None
    for n in range(4):
        try:
            r = S.get(url, timeout=timeout, allow_redirects=True)
            if r.status_code == 200: return r
            if r.status_code not in (429, 500, 502, 503, 504): r.raise_for_status()
        except Exception as e: err = e
        time.sleep(1.2 * (n + 1))
    raise RuntimeError(f"GET failed {url}: {err}")

def abs_url(v, page):
    v = v.strip().replace("&amp;", "&")
    if v.startswith("//"): v = "https:" + v
    return urllib.parse.urljoin(page, v)

def metrics(content):
    with Image.open(io.BytesIO(content)) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        w, h = im.size
        sm = im.copy(); sm.thumbnail((128, 128), Image.Resampling.LANCZOS)
        px = list(sm.getdata()); white = sum(r > 238 and g > 238 and b > 238 for r,g,b in px) / max(1, len(px))
        return w, h, white

def valid_img(url):
    try:
        r = get(url)
        if len(r.content) < 25000: return None
        w, h, white = metrics(r.content)
        ar = w / max(h, 1)
        if w < 550 or h < 350 or not .72 <= ar <= 3.2 or white > .76: return None
        return w, h, white
    except Exception:
        return None

def house_page(title, h1, text):
    head = (title + " " + h1).lower(); low = text.lower()
    if any(x in head for x in ("проект бани", "проект гаража", "проект беседки", "проект барбекю")): return False
    if re.search(r"\b(баня|гараж|беседка)\s*[-№]", head): return False
    return "тип строения жилой дом" in low or ("проект" in head and ("дома" in head or "дом " in head))

def metadata(title, h1, text):
    all_text = clean(title + " " + h1 + " " + text); low = all_text.lower()
    def first(patterns):
        for p in patterns:
            m = re.search(p, all_text, re.I)
            if m: return clean(m.group(1)).replace(".", ",").replace("x", "×").replace("х", "×")
        return ""
    area = first([r"Площадь\s+([\d.,]+)\s*м²", r"Общая площадь\s+([\d.,]+)\s*м²", r",\s*([\d.,]+)\s*м²"])
    dims = first([r"Габариты\s+([\d.,]+\s*[x×х]\s*[\d.,]+)", r"м²,\s*([\d.,]+\s*[x×х]\s*[\d.,]+)"])
    floors = first([r"Количество этажей\s+([1-4])", r"(?<!\d)([1-4])\s*(?:этаж|этажа|этажей)"])
    if not floors: floors = "1" if "одноэтаж" in low else "2" if "двухэтаж" in low else "3" if ("трехэтаж" in low or "трёхэтаж" in low) else ""
    material = ""
    for token, label in (("газобетон","газобетон"),("керамический блок","керамический блок"),("кирпич","кирпич"),("каркас","каркас"),("брус","брус"),("дерево","дерево"),("монолит","монолитный каркас")):
        if token in low: material = label; break
    style = ""
    for token, label in (("хай-тек","хай-тек"),("райта","стиль Райта"),("скандинав","скандинавский"),("европей","европейский"),("современн","современный"),("американ","американский"),("англий","английский"),("барнхаус","барнхаус"),("шале","шале")):
        if token in low: style = label; break
    feature = ""
    for token, label in (("с террасой","терраса"),("терраса да","терраса"),("гараж на 2","гараж на 2 авто"),("с гаражом","гараж"),("панорам","панорамные окна"),("плоская крыша","плоская крыша"),("мансард","мансарда"),("второй свет","второй свет"),("с сауной","сауна"),("с бассейном","бассейн"),("эркер да","эркер"),("балкон да","балкон")):
        if token in low: feature = label; break
    return area, dims, floors, material, style, feature

def extract_image(soup, html, page, project):
    options = []
    def add(v, score, origin, context=""):
        if not v: return
        u = abs_url(v, page)
        if "catalog-plans.ru/files/" not in u.lower() or not re.search(r"\.(?:jpe?g|png|webp|avif)(?:\?|$)", u, re.I): return
        options.append((score, u, origin, clean(context)[:400]))
    for sel, score, origin in (("meta[property='og:image']",1200,"og:image"),("meta[name='twitter:image']",1100,"twitter:image"),("link[rel='image_src']",1050,"image_src")):
        for t in soup.select(sel): add(t.get("content") or t.get("href"), score, origin, str(t))
    for t in soup.find_all(("img","source","a")):
        ctx = " ".join([t.get("alt", ""), t.get("title", ""), " ".join(t.get("class", [])), t.get("id", "")])
        par = t.parent
        for _ in range(2):
            if not par: break
            ctx += " " + " ".join(par.get("class", [])) + " " + par.get("id", "")
            par = par.parent
        low = ctx.lower(); score = 250
        if project.lower() in low or "проект" in low: score += 350
        if any(x in low for x in ("gallery","slider","swiper","visual","main","hero","fancybox")): score += 220
        if any(x in low for x in ("plan","floor","план","поэтаж","scheme","drawing","чертеж","passport","document","texture","material","logo","icon")): score -= 900
        if "facade" in low or "фасад" in low: score -= 350
        for a in ("src","data-src","data-lazy","data-original","data-full","href"): add(t.get(a), score, f"tag:{t.name}:{a}", ctx)
        for srcset in (t.get("srcset"), t.get("data-srcset")):
            if srcset:
                for part in srcset.split(","): add(part.strip().split(" ")[0], score + 30, f"tag:{t.name}:srcset", ctx)
    for u in FILE_RE.findall(html): add(u, 50, "html-regex")
    for u in REL_RE.findall(html): add(u, 45, "html-regex-relative")
    seen = set(); unique = []
    for item in sorted(options, reverse=True):
        if item[1] not in seen: seen.add(item[1]); unique.append(item)
    checked = []
    for score, u, origin, ctx in unique[:14]:
        m = valid_img(u)
        if not m: continue
        w, h, white = m
        final = score + min(math.log10(w*h)*35, 230) + (55 if 1.15 <= w/h <= 2.25 else 0) - white*330
        checked.append((final, u, origin, ctx, w, h, white))
        if origin == "og:image" and white < .62: return checked[-1]
    return max(checked, default=None)

def process(project):
    page = f"{SITE}/catalog/{project}"
    try: r = get(page)
    except Exception as e: print("SKIP", project, e, flush=True); return None
    r.encoding = r.apparent_encoding or r.encoding
    soup = BeautifulSoup(r.text, "html.parser")
    title = clean(soup.title.get_text(" ", strip=True) if soup.title else "")
    h1tag = soup.find("h1"); h1 = clean(h1tag.get_text(" ", strip=True) if h1tag else "")
    text = clean(soup.get_text(" ", strip=True))
    if not house_page(title, h1, text): print("SKIP", project, "not house", title, flush=True); return None
    selected = extract_image(soup, r.text, page, project)
    if not selected: print("SKIP", project, "no visualization", flush=True); return None
    score,u,origin,ctx,w,h,white = selected
    area,dims,floors,material,style,feature = metadata(title,h1,text)
    print(f"OK {project} {origin} {w}x{h} white={white:.2f} {u}", flush=True)
    return Rec(project,page,title,h1,area,dims,floors,material,style,feature,u,w,h,round(white,4),origin,ctx)

def floor(f): return {"1":"1 этаж","2":"2 этажа","3":"3 этажа","4":"4 этажа"}.get(f,"")
def slug(text):
    tr=str.maketrans({"а":"a","б":"b","в":"v","г":"g","д":"d","е":"e","ё":"e","ж":"zh","з":"z","и":"i","й":"y","к":"k","л":"l","м":"m","н":"n","о":"o","п":"p","р":"r","с":"s","т":"t","у":"u","ф":"f","х":"h","ц":"c","ч":"ch","ш":"sh","щ":"sch","ъ":"","ы":"y","ь":"","э":"e","ю":"yu","я":"ya"})
    return re.sub(r"[^a-z0-9]+","-",text.lower().translate(tr)).strip("-")[:70]
def board(rec,i):
    opts=["Готовые проекты домов","Проекты домов с визуализациями","Фасады домов"]
    try: a=float(rec.area.replace(",",".")) if rec.area else 0
    except: a=0
    if a: opts.append("Дома до 100 м²" if a<100 else "Дома до 120 м²" if a<=120 else "Дома до 150 м²" if a<=150 else "Дома 150–200 м²" if a<=200 else "Дома 200–300 м²" if a<=300 else "Большие дома")
    if rec.floors=="1": opts.append("Одноэтажные дома")
    elif rec.floors=="2": opts.append("Двухэтажные дома")
    m=rec.material.lower(); s=rec.style.lower(); f=rec.feature.lower()
    if "газобет" in m: opts.append("Дома из газобетона")
    elif "кирп" in m or "керамич" in m: opts.append("Кирпичные дома")
    elif "каркас" in m: opts.append("Каркасные дома")
    elif "брус" in m or "дерев" in m: opts.append("Деревянные дома")
    for token,b in (("хай-тек","Дома в стиле хай-тек"),("райт","Дома в стиле Райта"),("скандинав","Скандинавские дома"),("европей","Европейские дома"),("соврем","Современные дома"),("американ","Американские дома")):
        if token in s: opts.append(b); break
    for token,b in (("террас","Дома с террасой"),("гараж","Дома с гаражом"),("панорам","Дома с панорамными окнами"),("плос","Дома с плоской крышей"),("мансард","Дома с мансардой"),("второй свет","Дома со вторым светом")):
        if token in f: opts.append(b); break
    opts=list(dict.fromkeys(opts)); return opts[i%len(opts)]
PANEL=[("Откройте планировку и проверьте размеры","Смотреть планировку","plans"),("Сравните фасады, этажи и характеристики","Открыть проект","compare"),("Проверьте, поместится ли дом на участке","Проверить размеры","site"),("Посмотрите все ракурсы и детали проекта","Все фасады","facades"),("Оцените проект перед расчётом строительства","Рассчитать","estimate"),("Проверьте планировку до запроса изменений","Изучить проект","changes")]
EYEBROW=["Готовый проект дома","Планы • фасады • размеры","Проект для осознанного выбора","Архитектура и планировка"]
def hero(r,i):
    v=[]
    if r.style and r.area:v.append(f"{r.style.capitalize()} дом {r.area} м²")
    if r.area and r.floors:v.append(f"Дом {r.area} м² • {floor(r.floors)}")
    if r.feature and r.area:v.append(f"Дом {r.area} м² • {r.feature}")
    if r.area:v.append(f"Дом площадью {r.area} м²")
    v.append("Дом, который стоит рассмотреть"); return v[i%len(v)][:74]
def card_url(r,i):
    panel,cta,intent=PANEL[i%len(PANEL)]
    p={"project":r.project,"img":r.image_url,"eyebrow":EYEBROW[i%len(EYEBROW)],"title":hero(r,i),"panel":panel,"cta":cta}
    if r.area:p["area"]=r.area
    if r.floors:p["floors"]=floor(r.floors)
    if r.dimensions:p["dims"]=r.dimensions
    if r.feature:p["feature"]=r.feature
    if r.style:p["style"]=r.style
    if r.material:p["material"]=r.material
    target=TEMPLATE+"?"+urllib.parse.urlencode(p)
    return "https://image.thum.io/get/width/1000/crop/1800/allowJPG/noanimate/maxAge/720/?url="+urllib.parse.quote(target,safe=""),intent
def desc(r):
    facts=[]
    if r.area:facts.append(f"{r.area} м²")
    if r.floors:facts.append(floor(r.floors))
    if r.dimensions:facts.append(f"габариты {r.dimensions} м")
    if r.material:facts.append(f"стены — {r.material}")
    if r.style:facts.append(f"стиль — {r.style}")
    if r.feature:facts.append(f"особенность — {r.feature}")
    t=f"Проект дома №{r.project}. На превью используется визуализация, извлечённая непосредственно со страницы этого проекта на catalog-plans.ru. В карточке доступны планы этажей, фасады, размеры и характеристики."
    if facts:t+=f" Параметры: {'; '.join(facts)}."
    return t+" Откройте проект и проверьте планировку для своего участка до заказа."
def kw(r,b):
    a=[f"проект дома {r.project}",f"проект №{r.project}",b,"готовый проект дома","планировка дома","фасады дома","дом с размерами","визуализация дома"]
    if r.area:a.append(f"дом {r.area} м²")
    if r.material:a.append(f"дом {r.material}")
    if r.style:a.append(f"дом {r.style}")
    if r.feature:a.append(f"дом {r.feature}")
    a.append("catalog-plans.ru"); return ", ".join(dict.fromkeys(a))[:500]
def contact(records,path):
    tw,th,lh,cols=240,165,28,4; rows=math.ceil(len(records)/cols); sheet=Image.new("RGB",(tw*cols,(th+lh)*rows),"white"); d=ImageDraw.Draw(sheet); font=ImageFont.load_default()
    for i,r in enumerate(records):
        x=(i%cols)*tw;y=(i//cols)*(th+lh)
        try:
            im=Image.open(io.BytesIO(get(r.image_url).content)); im=ImageOps.exif_transpose(im).convert("RGB"); sheet.paste(ImageOps.fit(im,(tw,th),Image.Resampling.LANCZOS),(x,y))
        except: d.rectangle((x,y,x+tw-1,y+th-1),fill="#ddd")
        d.rectangle((x,y+th,x+tw-1,y+th+lh-1),fill="#17211b");d.text((x+7,y+th+7),r.project,fill="white",font=font)
    sheet.save(path,quality=88,optimize=True)
def main():
    ids=[x.strip() for x in (ROOT/"projects_candidates.txt").read_text().splitlines() if re.fullmatch(r"\d{2}-[A-Za-z0-9]+",x.strip())]
    records=[]
    for pid in ids:
        r=process(pid)
        if r:records.append(r)
        if len(records)==200:break
        time.sleep(.12)
    if len(records)<200:raise RuntimeError(f"Only {len(records)} verified houses")
    (OUT/"selected_projects.json").write_text(json.dumps([asdict(r) for r in records],ensure_ascii=False,indent=2),encoding="utf-8")
    with (OUT/"image_audit.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(asdict(records[0]).keys()));w.writeheader();w.writerows(asdict(r) for r in records)
    contact(records,OUT/"contact_sheet_200.jpg")
    headers=["Title","Media URL","Pinterest board","Thumbnail","Description","Link","Publish date","Keywords"]
    rows=[]
    titles=["открыть планировку и размеры","фасады, планы и характеристики","проверить габариты для участка","посмотреть все ракурсы и этажи","сравнить перед выбором","перейти к расчёту строительства"]
    for i,r in enumerate(records):
        media,intent=card_url(r,i);b=board(r,i);pin=4912+i;q=urllib.parse.urlencode({"utm_source":"pinterest","utm_medium":"organic","utm_campaign":"generated_house_cards_verified_batch_27","utm_content":f"pin_{pin}_{r.project.lower()}_{intent}","utm_term":slug(b)})
        rows.append({"Title":f"Проект дома №{r.project}: {titles[i%len(titles)]}","Media URL":media,"Pinterest board":b,"Thumbnail":"","Description":desc(r),"Link":r.page_url+"?"+q,"Publish date":"","Keywords":kw(r,b)})
    assert len(rows)==200 and len({x['Media URL'] for x in rows})==200 and len({x['Link'] for x in rows})==200 and len({r.project for r in records})==200
    out=OUT/"catalog_plans_pinterest_house_cards_batch_26_FIXED_200.csv"
    with out.open("w",encoding="utf-8-sig",newline="") as f:w=csv.DictWriter(f,fieldnames=headers,lineterminator="\n");w.writeheader();w.writerows(rows)
    samples=[];sd=OUT/"sample_cards";sd.mkdir(exist_ok=True)
    for i,r in enumerate(records[:4]):
        u,_=card_url(r,i); item={"project":r.project,"ok":False}
        try:
            rr=get(u,90); im=Image.open(io.BytesIO(rr.content));im.load();item["size"]=f"{im.width}x{im.height}";item["ok"]=im.width>=900 and im.height>=1300;(sd/f"{i+1:02d}_{r.project}.jpg").write_bytes(rr.content)
        except Exception as e:item["error"]=str(e)
        samples.append(item);print("CARD",item,flush=True)
    (OUT/"sample_card_results.json").write_text(json.dumps(samples,ensure_ascii=False,indent=2),encoding="utf-8")
    if sum(x['ok'] for x in samples)<3:raise RuntimeError("Rendered card size validation failed")
    (OUT/"summary.json").write_text(json.dumps({"projects":200,"unique_images":200,"og_images":sum(r.image_origin=='og:image' for r in records),"sample_cards_ok":sum(x['ok'] for x in samples),"template":TEMPLATE},ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__":main()
