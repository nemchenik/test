from __future__ import annotations

import csv, hashlib, io, json, math, os, re, shutil, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

import audit_generate as old

ROOT = Path(__file__).parent
OUT = ROOT / "audit_output"
SRC = OUT / "source_images"
CARDS = ROOT / "generated_batch_27"
SAMPLES = OUT / "sample_cards"
for d in (OUT, SRC, CARDS, SAMPLES): d.mkdir(parents=True, exist_ok=True)
REPO = os.environ.get("GITHUB_REPOSITORY", "nemchenik/test")
BRANCH = os.environ.get("HEAD_BRANCH", "catalog-plans-pinterest-cards")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)


def clean(v): return re.sub(r"\s+", " ", v or "").strip()


def fetch_bytes(url):
    e = None
    for n in range(3):
        try:
            r = requests.get(url, headers={"User-Agent": UA, "Referer": "https://catalog-plans.ru/"}, timeout=35)
            r.raise_for_status()
            return r.content
        except Exception as x: e = x
    raise RuntimeError(f"download failed {url}: {e}")


def fit_round(im, size, radius):
    im = ImageOps.fit(im, size, Image.Resampling.LANCZOS).convert("RGBA")
    mask = Image.new("L", size, 0); d = ImageDraw.Draw(mask)
    d.rounded_rectangle((0, 0, *size), radius=radius, fill=255)
    out = Image.new("RGBA", size); out.paste(im, (0, 0), mask); return out


def wrap(draw, text, f, width, lines=2):
    words, out, cur = clean(text).split(), [], ""
    for word in words:
        test = (cur + " " + word).strip()
        if not cur or draw.textbbox((0,0), test, font=f)[2] <= width: cur = test
        else:
            out.append(cur); cur = word
            if len(out) == lines - 1: break
    if len(out) < lines:
        used = sum(len(x.split()) for x in out); rest = " ".join(words[used:])
        while rest and draw.textbbox((0,0), rest + "…", font=f)[2] > width: rest = rest[:-1].rstrip()
        out.append(rest + ("…" if rest != " ".join(words[used:]) else ""))
    return out[:lines]


def draw_lines(draw, xy, values, f, color, gap):
    x, y = xy
    for value in values:
        draw.text((x,y), value, font=f, fill=color)
        b = draw.textbbox((x,y), value, font=f); y += b[3]-b[1]+gap
    return y


def floor_text(v): return {"1":"1 этаж","2":"2 этажа","3":"3 этажа","4":"4 этажа"}.get(v, "")


PANELS = [
    ("Откройте планировку и проверьте размеры", "Смотреть планировку", "plans"),
    ("Сравните фасады, этажи и характеристики", "Открыть проект", "compare"),
    ("Проверьте, поместится ли дом на участке", "Проверить размеры", "site"),
    ("Посмотрите все ракурсы и детали проекта", "Все фасады", "facades"),
    ("Оцените проект перед расчётом строительства", "Рассчитать", "estimate"),
    ("Проверьте планировку до запроса изменений", "Изучить проект", "changes"),
]


def hero(r, i):
    v=[]
    if r.style and r.area: v.append(f"{r.style.capitalize()} дом {r.area} м²")
    if r.area and r.floors: v.append(f"Дом {r.area} м² • {floor_text(r.floors)}")
    if r.feature and r.area: v.append(f"Дом {r.area} м² • {r.feature}")
    if r.area: v.append(f"Дом площадью {r.area} м²")
    v.append("Дом, который стоит рассмотреть")
    return v[i % len(v)]


def render(r, i, source, target):
    W,H,P=1000,1500,925; ink="#17211B"; paper="#F5F1E9"; accent="#C86F45"
    src=Image.open(source); src=ImageOps.exif_transpose(src).convert("RGB")
    bg=ImageOps.fit(src,(W,P),Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(26))
    bg=Image.blend(bg,Image.new("RGB",bg.size,"#15201A"),.46)
    card=Image.new("RGBA",(W,H),ink); card.paste(bg,(0,0)); draw=ImageDraw.Draw(card)
    for y in range(P):
        a=max(int(105*max(0,1-y/250)),int(120*max(0,(y-680)/245)))
        draw.line((0,y,W,y),fill=(6,13,9,a))
    draw.text((48,45),"CATALOG PLANS",font=font(28,1),fill="white")
    pill=f"Проект №{r.project}"; pf=font(23,1); pw=draw.textbbox((0,0),pill,font=pf)[2]+44
    draw.rounded_rectangle((W-48-pw,34,W-48,90),radius=28,fill=(20,31,24,205),outline=(255,255,255,160),width=2)
    draw.text((W-48-pw+22,49),pill,font=pf,fill="white")
    shadow=Image.new("RGBA",(960,655)); sd=ImageDraw.Draw(shadow); sd.rounded_rectangle((20,20,940,635),radius=34,fill=(0,0,0,110)); shadow=shadow.filter(ImageFilter.GaussianBlur(18)); card.alpha_composite(shadow,(20,102))
    card.alpha_composite(fit_round(src,(920,615),30),(40,120)); draw=ImageDraw.Draw(card)
    draw.rounded_rectangle((40,120,960,735),radius=30,outline=(255,255,255,90),width=2)
    draw.text((48,778),["ГОТОВЫЙ ПРОЕКТ ДОМА","ПЛАНЫ • ФАСАДЫ • РАЗМЕРЫ","ПРОЕКТ ДЛЯ ОСОЗНАННОГО ВЫБОРА","АРХИТЕКТУРА И ПЛАНИРОВКА"][i%4],font=font(19,1),fill="#F2EEE7")
    draw_lines(draw,(48,812),wrap(draw,hero(r,i),font(43,1),890,2),font(43,1),"white",7)
    panel=Image.new("RGBA",(W,H-P)); pd=ImageDraw.Draw(panel); pd.rounded_rectangle((0,0,W,H-P+60),radius=48,fill=paper); card.alpha_composite(panel,(0,P)); draw=ImageDraw.Draw(card)
    draw.rounded_rectangle((48,966,120,974),radius=4,fill=accent)
    panel_text,cta,intent=PANELS[i%len(PANELS)]
    draw_lines(draw,(48,1001),wrap(draw,panel_text,font(46,1),880,2),font(46,1),ink,8)
    chips=[]
    if r.area: chips.append(f"{r.area} м²")
    if r.floors: chips.append(floor_text(r.floors))
    if r.dimensions: chips.append(f"{r.dimensions} м")
    if r.feature: chips.append(r.feature)
    if r.style: chips.append(r.style)
    if r.material: chips.append(r.material)
    x,y=48,1183; cf=font(20,1)
    for chip in chips[:3]:
        cw=draw.textbbox((0,0),chip,font=cf)[2]+34
        if x+cw>952: break
        draw.rounded_rectangle((x,y,x+cw,y+48),radius=24,fill="white",outline="#D5CDC0")
        draw.text((x+17,y+11),chip,font=cf,fill=ink); x+=cw+12
    draw.text((48,1400),"catalog-plans.ru",font=font(22,1),fill="#667068")
    box=(566,1360,952,1442); draw.rounded_rectangle(box,radius=18,fill=accent); label=cta+"  →"; tf=font(23,1); b=draw.textbbox((0,0),label,font=tf)
    draw.text((box[0]+(box[2]-box[0]-b[2])/2,box[1]+(box[3]-box[1]-(b[3]-b[1]))/2-3),label,font=tf,fill="white")
    card.convert("RGB").save(target,"JPEG",quality=86,optimize=True,progressive=True)
    return intent


def board(r,i):
    opts=["Готовые проекты домов","Проекты домов с визуализациями","Фасады домов"]
    try:a=float(r.area.replace(",",".")) if r.area else 0
    except:a=0
    if a:opts.append("Дома до 100 м²" if a<100 else "Дома до 120 м²" if a<=120 else "Дома до 150 м²" if a<=150 else "Дома 150–200 м²" if a<=200 else "Дома 200–300 м²" if a<=300 else "Большие дома")
    if r.floors=="1":opts.append("Одноэтажные дома")
    elif r.floors=="2":opts.append("Двухэтажные дома")
    m,s,f=r.material.lower(),r.style.lower(),r.feature.lower()
    if "газобет" in m:opts.append("Дома из газобетона")
    elif "кирп" in m or "керамич" in m:opts.append("Кирпичные дома")
    elif "каркас" in m:opts.append("Каркасные дома")
    elif "брус" in m or "дерев" in m:opts.append("Деревянные дома")
    for t,b in (("хай-тек","Дома в стиле хай-тек"),("райт","Дома в стиле Райта"),("скандинав","Скандинавские дома"),("европей","Европейские дома"),("соврем","Современные дома"),("американ","Американские дома")):
        if t in s:opts.append(b);break
    for t,b in (("террас","Дома с террасой"),("гараж","Дома с гаражом"),("панорам","Дома с панорамными окнами"),("плос","Дома с плоской крышей"),("мансард","Дома с мансардой"),("второй свет","Дома со вторым светом")):
        if t in f:opts.append(b);break
    opts=list(dict.fromkeys(opts)); seed=int(hashlib.sha1(r.project.encode()).hexdigest()[:8],16); return opts[(seed+i)%len(opts)]


def slug(text):
    tr=str.maketrans({"а":"a","б":"b","в":"v","г":"g","д":"d","е":"e","ё":"e","ж":"zh","з":"z","и":"i","й":"y","к":"k","л":"l","м":"m","н":"n","о":"o","п":"p","р":"r","с":"s","т":"t","у":"u","ф":"f","х":"h","ц":"c","ч":"ch","ш":"sh","щ":"sch","ъ":"","ы":"y","ь":"","э":"e","ю":"yu","я":"ya"})
    return re.sub(r"[^a-z0-9]+","-",text.lower().translate(tr)).strip("-")[:70]


def desc(r):
    facts=[]
    if r.area:facts.append(f"{r.area} м²")
    if r.floors:facts.append(floor_text(r.floors))
    if r.dimensions:facts.append(f"габариты {r.dimensions} м")
    if r.material:facts.append(f"стены — {r.material}")
    if r.style:facts.append(f"стиль — {r.style}")
    if r.feature:facts.append(f"особенность — {r.feature}")
    v=f"Проект дома №{r.project}. На превью показана каноническая визуализация, взятая непосредственно со страницы этого проекта на catalog-plans.ru. В карточке доступны планы этажей, фасады, размеры и характеристики."
    if facts:v+=f" Параметры: {'; '.join(facts)}."
    return (v+" Откройте проект, проверьте планировку и сопоставьте габариты со своим участком до заказа.")[:500]


def keywords(r,b):
    v=[f"проект дома {r.project}",f"проект №{r.project}",b,"готовый проект дома","планировка дома","фасады дома","дом с размерами","визуализация дома"]
    if r.area:v.append(f"дом {r.area} м²")
    if r.material:v.append(f"дом {r.material}")
    if r.style:v.append(f"дом {r.style}")
    if r.feature:v.append(f"дом {r.feature}")
    v.append("catalog-plans.ru");return ", ".join(dict.fromkeys(v))[:500]


def contact(records):
    tw,th,lh,cols=180,270,26,5; rows=math.ceil(len(records)/cols); sheet=Image.new("RGB",(tw*cols,(th+lh)*rows),"white"); d=ImageDraw.Draw(sheet); f=font(14,1)
    for i,r in enumerate(records):
        x=(i%cols)*tw;y=(i//cols)*(th+lh);im=Image.open(CARDS/f"{r.project}.jpg");sheet.paste(ImageOps.fit(im,(tw,th),Image.Resampling.LANCZOS),(x,y));d.rectangle((x,y+th,x+tw,y+th+lh),fill="#17211B");d.text((x+6,y+th+5),r.project,font=f,fill="white")
    sheet.save(OUT/"contact_sheet_200.jpg","JPEG",quality=88,optimize=True)


def main():
    ids=[x.strip() for x in (ROOT/"projects_candidates.txt").read_text().splitlines() if re.fullmatch(r"\d{2}-[A-Za-z0-9]+",x.strip())]
    results={}
    with ThreadPoolExecutor(max_workers=8) as ex:
        fs={ex.submit(old.process,p):p for p in ids}
        for f in as_completed(fs):
            p=fs[f]
            try:results[p]=f.result()
            except Exception as e:print("SKIP",p,e,flush=True);results[p]=None
    records=[];seen=set()
    for p in ids:
        r=results.get(p)
        if not r or r.image_origin!="og:image" or r.white_ratio>.55 or r.image_width<900 or not 1.25<=r.image_width/r.image_height<=1.85 or r.image_url in seen:continue
        records.append(r);seen.add(r.image_url)
        if len(records)==200:break
    if len(records)<200:raise RuntimeError(f"Only {len(records)} exact unique house images")
    for d in (SRC,CARDS,SAMPLES):
        for p in d.glob("*.jpg"):p.unlink()
    def dl(r):
        data=fetch_bytes(r.image_url);path=SRC/f"{r.project}.jpg";ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB").save(path,"JPEG",quality=92,optimize=True);return r.project
    with ThreadPoolExecutor(max_workers=8) as ex:
        for f in as_completed([ex.submit(dl,r) for r in records]):f.result()
    intents={}
    for i,r in enumerate(records):
        path=CARDS/f"{r.project}.jpg";intents[r.project]=render(r,i,SRC/f"{r.project}.jpg",path)
        with Image.open(path) as im:assert im.size==(1000,1500)
        if i<8:shutil.copy2(path,SAMPLES/path.name)
    base=f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/pinterest/generated_batch_27";headers=["Title","Media URL","Pinterest board","Thumbnail","Description","Link","Publish date","Keywords"]
    tv=["открыть планировку и размеры","фасады, планы и характеристики","проверить габариты для участка","посмотреть все ракурсы и этажи","сравнить перед выбором","перейти к расчёту строительства"]
    rows=[]
    for i,r in enumerate(records):
        b=board(r,i);pin=4912+i;q=urllib.parse.urlencode({"utm_source":"pinterest","utm_medium":"organic","utm_campaign":"generated_house_cards_verified_batch_27","utm_content":f"pin_{pin}_{r.project.lower()}_{intents[r.project]}","utm_term":slug(b)})
        rows.append({"Title":f"Проект дома №{r.project}: {tv[i%6]}","Media URL":f"{base}/{r.project}.jpg","Pinterest board":b,"Thumbnail":"","Description":desc(r),"Link":r.page_url+"?"+q,"Publish date":"","Keywords":keywords(r,b)})
    assert len(rows)==200 and len({x['Media URL'] for x in rows})==200 and len({x['Link'] for x in rows})==200
    name="catalog_plans_pinterest_house_cards_batch_26_FIXED_200.csv"
    for path in (OUT/name,CARDS/name):
        with path.open("w",encoding="utf-8-sig",newline="") as f:w=csv.DictWriter(f,fieldnames=headers,lineterminator="\n");w.writeheader();w.writerows(rows)
    with (OUT/"image_audit.csv").open("w",encoding="utf-8-sig",newline="") as f:
        fields=list(vars(records[0]).keys());w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(vars(r) for r in records)
    contact(records);(OUT/"summary.json").write_text(json.dumps({"projects":200,"unique_source_images":200,"generated_cards":200,"card_size":"1000x1500","image_origin":"canonical og:image from exact project page","campaign":"generated_house_cards_verified_batch_27","branch":BRANCH},ensure_ascii=False,indent=2))
    print("SUCCESS 200 verified cards",flush=True)


if __name__=="__main__":main()
