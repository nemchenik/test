from __future__ import annotations

import ast
import base64
import gzip
from pathlib import Path


ROOT = Path(__file__).parent
BOOTSTRAP = ROOT / "batch36_house_plan_facade_video_bootstrap.py"


def embedded_batch36_source() -> str:
    """Return the checked batch-36 implementation without executing it."""
    tree = ast.parse(BOOTSTRAP.read_text(encoding="utf-8"), filename=str(BOOTSTRAP))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "PAYLOAD"
            for target in node.targets
        ):
            payload = ast.literal_eval(node.value)
            if isinstance(payload, str):
                return gzip.decompress(base64.b64decode(payload)).decode("utf-8")
    raise RuntimeError("PAYLOAD was not found in batch36 bootstrap")


def replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise RuntimeError(
            f"Expected one source fragment, found {source.count(old)}: {old[:120]!r}"
        )
    return source.replace(old, new, 1)


source = embedded_batch36_source()

# Use a cinematic sequence for this collection:
# main project visualization -> floor plans -> facades.
source = replace_once(
    source,
    '''        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-loop", "1", "-t", str(STAGE_SECONDS), "-i", str(static_card),
        "-loop", "1", "-t", str(STAGE_SECONDS), "-i", str(plan_slide),
        "-loop", "1", "-t", str(STAGE_SECONDS), "-i", str(facade_slide),
        "-loop", "1", "-t", str(STAGE_SECONDS), "-i", str(static_card),
''',
    '''        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-loop", "1", "-t", str(STAGE_SECONDS), "-i", str(static_card),
        "-loop", "1", "-t", str(STAGE_SECONDS), "-i", str(plan_slide),
        "-loop", "1", "-t", str(STAGE_SECONDS), "-i", str(facade_slide),
''',
)
source = replace_once(
    source,
    '''        "-map", "[outv]", "-an",
''',
    '''        "-map", "[outv]", "-t", "7.40", "-an",
''',
)

for old, new in {
    'OUT_DIR = ROOT / "batch36_video_output"': 'OUT_DIR = ROOT / "batch44_video_output"',
    'WORK_DIR = ROOT / "batch36_video_work"': 'WORK_DIR = ROOT / "batch44_video_work"',
    'STATIC_DIR = ASSET_CHECKOUT / "pinterest" / "generated_batch_34_color_static"':
        'STATIC_DIR = WORK_DIR / "house_slides"',
    'VIDEO_DIR = ASSET_CHECKOUT / "pinterest" / "generated_batch_36_house_plan_facade_video"':
        'VIDEO_DIR = ASSET_CHECKOUT / "pinterest" / "generated_batch_44_modern_minimal_video"',
    'CAMPAIGN = "generated_house_plan_facade_video_batch_36"':
        'CAMPAIGN = "generated_modern_minimal_video_batch_44"',
    'START_PIN = 6512': 'START_PIN = 8112',
    'STAGE_SECONDS = 2.0': 'STAGE_SECONDS = 2.8',
    'EXPECTED_DURATION_MIN = 6.35': 'EXPECTED_DURATION_MIN = 7.20',
    'EXPECTED_DURATION_MAX = 6.85': 'EXPECTED_DURATION_MAX = 7.60',
    '"duration_seconds": "6.35-6.85"': '"duration_seconds": "7.20-7.60"',
    'f"pinterest/generated_batch_36_house_plan_facade_video/{record.project}.mp4"':
        'f"pinterest/generated_batch_44_modern_minimal_video/{record.project}.mp4"',
    '"local_validation_batch36.json"': '"local_validation_batch44.json"',
    '"public_validation_batch36.json"': '"public_validation_batch44.json"',
}.items():
    source = replace_once(source, old, new)

old_csv_name = '"catalog_plans_pinterest_house_plan_facade_videos_batch_36_200.csv"'
if source.count(old_csv_name) != 2:
    raise RuntimeError(f"Expected two batch36 CSV references, found {source.count(old_csv_name)}")
source = source.replace(
    old_csv_name,
    '"catalog_plans_pinterest_modern_minimal_videos_batch_44_200.csv"',
)

source = replace_once(
    source,
    '''    feature: str
    plan_urls: list[str]
''',
    '''    feature: str
    image_url: str
    plan_urls: list[str]
''',
)

old_project_ids = '''def project_ids() -> list[str]:
    if not STATIC_DIR.exists():
        raise RuntimeError(f"Static card directory not found: {STATIC_DIR}")
    ids = sorted(path.stem for path in STATIC_DIR.glob("*.jpg") if PROJECT_RE.fullmatch(path.stem))
    if len(ids) != 200:
        raise RuntimeError(f"Expected 200 static cards, found {len(ids)}")
    return ids
'''
new_project_ids = '''PROJECT_CACHE: dict[str, ProjectMedia] = {}


def random_catalog_project_ids() -> list[str]:
    response = old.S.get("https://catalog-plans.ru/sitemap.xml", timeout=60)
    response.raise_for_status()
    values = re.findall(r"<loc>https://catalog-plans\\.ru/catalog/([^<]+)</loc>", response.text, re.I)
    result = []
    seen = set()
    for value in values:
        project = urllib.parse.unquote(value).strip("/")
        if PROJECT_RE.fullmatch(project) and project not in seen:
            seen.add(project)
            result.append(project)
    if len(result) < 1000:
        raise RuntimeError(f"Catalog sitemap yielded only {len(result)} project IDs")
    # Stable pseudo-random order: reruns select the same valid projects.
    result.sort(key=lambda value: __import__("hashlib").sha256(("batch44|" + value).encode()).digest())
    print(f"randomized catalog projects found: {len(result)}", flush=True)
    return result


def published_video_ids() -> set[str]:
    url = f"https://api.github.com/repos/{REPO}/git/trees/{ASSET_BRANCH}?recursive=1"
    response = old.S.get(url, timeout=60)
    response.raise_for_status()
    payload = response.json()
    if payload.get("truncated"):
        raise RuntimeError("GitHub asset tree is truncated; cannot safely prevent duplicates")
    result = set()
    for item in payload.get("tree", []):
        path = item.get("path", "")
        if path.startswith("pinterest/generated_batch_") and path.lower().endswith(".mp4"):
            result.add(Path(path).stem)
    return result


def project_ids() -> list[str]:
    prepared = sorted(
        path.stem for path in STATIC_DIR.glob("*.jpg")
        if PROJECT_RE.fullmatch(path.stem)
    )
    if len(prepared) == 200 and len(set(prepared)) == 200:
        print("reusing 200 previously selected random project IDs", flush=True)
        return prepared

    seed_csv = OUT_DIR / "catalog_plans_pinterest_modern_minimal_videos_batch_44_200.csv"
    if seed_csv.exists():
        with seed_csv.open("r", encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))
        seeded = [Path(urllib.parse.urlsplit(row["Media URL"]).path).stem for row in rows]
        if len(seeded) != 200 or len(set(seeded)) != 200 or not all(PROJECT_RE.fullmatch(item) for item in seeded):
            raise RuntimeError(f"Invalid batch44 seed CSV: {seed_csv}")
        print("using 200 stable project IDs from the batch44 seed CSV", flush=True)
        return seeded

    excluded = published_video_ids()
    all_projects = random_catalog_project_ids()
    candidates = []
    seen = set()
    for project in all_projects:
        if project not in excluded and project not in seen:
            seen.add(project)
            candidates.append(project)
    selected = []
    batch_size = 64
    for offset in range(0, len(candidates), batch_size):
        batch = candidates[offset:offset + batch_size]
        results = {}
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(process_project, project): project for project in batch}
            for future in as_completed(futures):
                project = futures[future]
                try:
                    results[project] = future.result()
                except Exception as exc:
                    print(f"SKIP {project}: {exc}", flush=True)
        for project in batch:
            record = results.get(project)
            if record is None:
                continue
            PROJECT_CACHE[project] = record
            selected.append(project)
            if len(selected) == 200:
                print(
                    f"selected 200 new projects; excluded {len(excluded)} existing video IDs",
                    flush=True,
                )
                return selected
        print(f"eligible projects selected {len(selected)}/200", flush=True)
    raise RuntimeError(f"Only {len(selected)} new projects have valid house, plan and facade media")
'''
source = replace_once(source, old_project_ids, new_project_ids)

source = replace_once(
    source,
    '''def process_project(project: str) -> ProjectMedia:
    record = old.process(project)
''',
    '''def process_project(project: str) -> ProjectMedia:
    if project in PROJECT_CACHE:
        return PROJECT_CACHE[project]
    record = old.process(project)
''',
)
source = replace_once(
    source,
    '''    response = old.get(record.page_url)
    response.encoding = response.apparent_encoding or response.encoding
    soup = BeautifulSoup(response.text, "html.parser")

    plan_urls = section_urls(soup, ".media-tile--plan", record.page_url)
''',
    '''    response = old.get(record.page_url)
    response.encoding = response.apparent_encoding or response.encoding
    soup = BeautifulSoup(response.text, "html.parser")

    og_image = soup.select_one('meta[property="og:image"]')
    image_url = urllib.parse.urljoin(
        record.page_url,
        og_image.get("content", "") if og_image else record.image_url,
    )
    fetch_image(image_url)

    plan_urls = section_urls(soup, ".media-tile--plan", record.page_url)
''',
)
source = replace_once(
    source,
    '''        feature=record.feature,
        plan_urls=plan_urls,
''',
    '''        feature=record.feature,
        image_url=image_url,
        plan_urls=plan_urls,
''',
)
source = replace_once(
    source,
    '''def fetch_image(url: str) -> bytes:
    error: Exception | None = None
''',
    '''IMAGE_CACHE: dict[str, bytes] = {}


def fetch_image(url: str) -> bytes:
    if url in IMAGE_CACHE:
        return IMAGE_CACHE[url]
    error: Exception | None = None
''',
)
source = replace_once(
    source,
    '''            with Image.open(io.BytesIO(data)) as image:
                image.verify()
            return data
''',
    '''            with Image.open(io.BytesIO(data)) as image:
                image.verify()
            IMAGE_CACHE[url] = data
            return data
''',
)
source = replace_once(
    source,
    '''    plan_urls = section_urls(soup, ".media-tile--plan", record.page_url)
    facade_urls = section_urls(soup, ".media-tile--facade", record.page_url)

    if not plan_urls:
''',
    '''    plan_urls = section_urls(soup, ".media-tile--plan", record.page_url)
    facade_urls = section_urls(soup, ".media-tile--facade", record.page_url)

    def downloadable(urls: list[str], needed: int, maximum: int) -> list[str]:
        verified = []
        for url in urls:
            try:
                fetch_image(url)
                verified.append(url)
            except Exception:
                continue
            if len(verified) == maximum:
                break
        return verified if len(verified) >= needed else []

    plan_urls = downloadable(plan_urls, 1, 2)
    facade_urls = downloadable(facade_urls, 2, 4)

    if not plan_urls:
''',
)

house_renderer = '''

def render_house_slide(record: ProjectMedia, index: int, target: Path) -> None:
    data = fetch_image(record.image_url)
    source_image = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
    canvas = Image.new("RGB", (720, 1080), "#FFFFFF")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((34, 0, 38, 1080), fill="#36454F")
    draw.text((64, 38), "АРХИТЕКТУРНЫЙ ПРОЕКТ", font=font(15, True), fill="#36454F")
    draw.text((64, 92), "I", font=font(54, False), fill="#FFFFFF")
    number = f"№ {record.project}"
    number_w = draw.textbbox((0, 0), number, font=font(28, True))[2]
    draw.text((672 - number_w, 42), number, font=font(28, True), fill="#1F2933")
    draw.line((64, 82, 672, 82), fill="#D3D3D3", width=1)

    hero = ImageOps.fit(source_image, (580, 520), Image.Resampling.LANCZOS)
    canvas.paste(hero, (92, 166))
    draw.rectangle((82, 156, 672, 696), outline="#36454F", width=2)
    draw.rectangle((92, 634, 330, 686), fill="#FFFFFF")
    draw.text((112, 651), "ОБЛИК ДОМА", font=font(13, True), fill="#36454F")

    title_options = [
        f"Дом {record.area} м²: архитектура без лишнего" if record.area else "Архитектура без лишнего",
        f"Проект №{record.project}: форма и функция",
        "Планы, фасады и точные пропорции",
        "Современный проект в деталях",
    ]
    draw_footer(draw, record, title_options[index % len(title_options)], "#36454F")
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, "PNG", optimize=True)
'''
source = replace_once(
    source,
    '\n\ndef render_plan_slide(record: ProjectMedia, plan_paths: list[Path], target: Path) -> None:',
    house_renderer + '\n\ndef render_plan_slide(record: ProjectMedia, plan_paths: list[Path], target: Path) -> None:',
)

source = replace_once(
    source,
    '''    for directory in (OUT_DIR, WORK_DIR, MEDIA_DIR, PLAN_DIR, FACADE_DIR, VIDEO_DIR):
''',
    '''    for directory in (OUT_DIR, WORK_DIR, MEDIA_DIR, PLAN_DIR, FACADE_DIR, STATIC_DIR, VIDEO_DIR):
''',
)
source = replace_once(
    source,
    '''    def prepare(record: ProjectMedia) -> str:
        plan_paths, facade_paths = download_project_media(record)
        render_plan_slide(record, plan_paths, PLAN_DIR / f"{record.project}.png")
''',
    '''    def prepare(record: ProjectMedia) -> str:
        plan_paths, facade_paths = download_project_media(record)
        render_house_slide(record, ids.index(record.project), STATIC_DIR / f"{record.project}.jpg")
        render_plan_slide(record, plan_paths, PLAN_DIR / f"{record.project}.png")
''',
)

# Cool blueprint palette distinguishes this series from the earlier warm editorial videos.
for old, new in {
    'Image.new("RGB", (720, 1080), "#08140F")': 'Image.new("RGB", (720, 1080), "#EAF4F8")',
    'Image.new("RGB", (720, 1080), "#0B1512")': 'Image.new("RGB", (720, 1080), "#DCECF2")',
    '"РЕАЛЬНЫЕ ПЛАНИРОВКИ ПРОЕКТА"': '"ЧЕРТЁЖ / ПЛАНИРОВКА"',
    '"РЕАЛЬНЫЕ ФАСАДЫ ПРОЕКТА"': '"ОСТЕКЛЁННЫЕ ФАСАДЫ / 4 РАКУРСА"',
    '"ДОМ  →  ПЛАНИРОВКИ"': '"01  /  ЧЕРТЁЖ И СВЕТОВЫЕ ЗОНЫ"',
    '"ПЛАНИРОВКИ  →  ФАСАДЫ"': '"03  /  СРАВНЕНИЕ ФАСАДОВ"',
    '"Посмотрите, как устроены этажи дома"': '"Где окна раскрывают пространство?"',
    '"Оцените архитектуру дома со всех сторон"': '"Сравните остекление на фасадах"',
}.items():
    source = replace_once(source, old, new)
source = source.replace('"#F3EEE5"', '"#FFFFFF"')
source = source.replace('"#1B2A25"', '"#092D42"')
source = source.replace('"#D7C9B7"', '"#18738C"')
source = source.replace('"#C86F45"', '"#00A6C8"')
source = source.replace('"#B56A45"', '"#006781"')
source = source.replace('"#F8F5EF"', '"#092D42"')
source = source.replace('"#1A3026"', '"#00A6C8"')
source = source.replace('"#243B32"', '"#092D42"')
source = source.replace('"#D8D0C5"', '"#79B9CA"')
source = source.replace('"CATALOG PLANS"', '"КАТАЛОГ ПРОЕКТОВ"')

old_filter = '''def ffmpeg_filter() -> str:
    return (
        f"[0:v]scale=720:1080,zoompan=z='min(zoom+0.00055,1.045)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={STAGE_FRAMES}:s=720x1080:fps={FPS},setsar=1[v0];"
        f"[1:v]scale=720:1080,zoompan=z='min(zoom+0.00035,1.025)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={STAGE_FRAMES}:s=720x1080:fps={FPS},setsar=1[v1];"
        f"[2:v]scale=720:1080,zoompan=z='if(eq(on,0),1.025,max(1.0,zoom-0.00030))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={STAGE_FRAMES}:s=720x1080:fps={FPS},setsar=1[v2];"
        f"[3:v]scale=720:1080,zoompan=z='1.015+0.006*sin(on/10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={STAGE_FRAMES}:s=720x1080:fps={FPS},setsar=1[v3];"
        "[v0][v1]xfade=transition=wipeleft:duration=0.45:offset=1.55[x1];"
        "[x1][v2]xfade=transition=slideleft:duration=0.45:offset=3.10[x2];"
        "[x2][v3]xfade=transition=fade:duration=0.45:offset=4.65,"
        "fade=t=in:st=0:d=0.20,fade=t=out:st=6.20:d=0.45,scale=in_range=pc:out_range=tv,format=yuv420p[outv]"
    )
'''
new_filter = '''def ffmpeg_filter() -> str:
    return (
        f"[0:v]scale=720:1080,zoompan=z='min(zoom+0.00050,1.045)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={STAGE_FRAMES}:s=720x1080:fps={FPS},setsar=1[v0];"
        f"[1:v]scale=720:1080,zoompan=z='if(eq(on,0),1.035,max(1.0,zoom-0.00042))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={STAGE_FRAMES}:s=720x1080:fps={FPS},setsar=1[v1];"
        f"[2:v]scale=720:1080,zoompan=z='1.012+0.005*sin(on/10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={STAGE_FRAMES}:s=720x1080:fps={FPS},setsar=1[v2];"
        "[v0][v1]xfade=transition=wipeup:duration=0.50:offset=2.30[x1];"
        "[x1][v2]xfade=transition=fadeblack:duration=0.50:offset=4.60,"
        "fade=t=in:st=0:d=0.16,fade=t=out:st=7.00:d=0.35,scale=in_range=pc:out_range=tv,format=yuv420p[outv]"
    )
'''
source = replace_once(source, old_filter, new_filter)

seo_overrides = '''

def draw_header(draw: ImageDraw.ImageDraw, project: str, label: str) -> None:
    draw.rectangle((0, 0, 720, 126), fill="#FFFFFF")
    draw.rectangle((34, 0, 38, 126), fill="#36454F")
    draw.text((64, 30), label, font=font(15, True), fill="#36454F")
    number = f"ПРОЕКТ №{project}"
    width = draw.textbbox((0, 0), number, font=font(26, True))[2]
    draw.text((672 - width, 72), number, font=font(26, True), fill="#1F2933")
    draw.line((64, 106, 672, 106), fill="#D3D3D3", width=1)


def draw_footer(draw: ImageDraw.ImageDraw, record: ProjectMedia, title: str, accent: str) -> None:
    draw.rectangle((0, 748, 720, 1080), fill="#FFFFFF")
    draw.text((64, 786), "КРАТКО О ПРОЕКТЕ", font=font(13, True), fill=accent)
    title_font = font(30, False)
    lines = wrap_text(draw, title, title_font, 630, 2)
    y = 830
    for line in lines:
        draw.text((64, y), line, font=title_font, fill="#1F2933")
        y += 38
    chips = []
    if record.area:
        chips.append(f"{record.area} м²")
    if record.floors:
        chips.append(floor_text(record.floors))
    if record.dimensions:
        chips.append(f"{record.dimensions} м")
    x = 64
    for chip in chips[:3]:
        chip_font = font(16, True)
        width = draw.textbbox((0, 0), chip, font=chip_font)[2] + 28
        draw.line((x, 951, x + width, 951), fill="#36454F", width=1)
        draw.text((x + 4, 964), chip, font=chip_font, fill="#FFFFFF")
        x += width + 8
    draw.line((64, 1020, 672, 1020), fill="#D3D3D3", width=1)
    draw.text((64, 1038), "catalog-plans.ru", font=font(15, True), fill="#708090")
    footer = "визуализация  •  планы  •  фасады"
    width = draw.textbbox((0, 0), footer, font=font(16, True))[2]
    draw.text((672 - width, 1038), footer, font=font(15, True), fill="#36454F")


def render_plan_slide(record: ProjectMedia, plan_paths: list[Path], target: Path) -> None:
    canvas = Image.new("RGB", (720, 1080), "#F1F3F4")
    draw = ImageDraw.Draw(canvas)
    draw_header(draw, record.project, "ПЛАНИРОВКА ДОМА")
    paths = plan_paths[:2]
    boxes = [(48, 148, 624, 552)] if len(paths) == 1 else [(42, 148, 310, 552), (368, 148, 310, 552)]
    for index, (path, box) in enumerate(zip(paths, boxes, strict=False), start=1):
        image = Image.open(path)
        fitted = fit_contain(image, (box[2], box[3]), padding=22, background="#FFFFFF")
        canvas.paste(fitted, (box[0], box[1]))
        draw.rectangle((box[0], box[1], box[0] + box[2], box[1] + box[3]), outline="#36454F", width=2)
        draw.text((box[0] + 18, box[1] + 14), f"{index:02d}", font=font(15, True), fill="#FFFFFF")
    draw.text((64, 716), "II   ПЛАНИРОВОЧНЫЕ РЕШЕНИЯ", font=font(15, True), fill="#36454F")
    draw_footer(draw, record, "Планировка и пропорции", "#36454F")
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, "PNG", optimize=True)


def render_facade_slide(record: ProjectMedia, facade_paths: list[Path], target: Path) -> None:
    canvas = Image.new("RGB", (720, 1080), "#F1F3F4")
    draw = ImageDraw.Draw(canvas)
    draw_header(draw, record.project, "ФАСАДЫ В ДЕТАЛЯХ")
    paths = facade_paths[:4]
    if len(paths) == 2:
        boxes = [(42, 150, 636, 260), (42, 430, 636, 260)]
    elif len(paths) == 3:
        boxes = [(42, 150, 310, 250), (368, 150, 310, 250), (205, 420, 310, 250)]
    else:
        boxes = [(42, 145, 310, 258), (368, 145, 310, 258), (42, 419, 310, 258), (368, 419, 310, 258)]
    for index, (path, box) in enumerate(zip(paths, boxes, strict=False), start=1):
        image = Image.open(path)
        fitted = fit_contain(image, (box[2], box[3]), padding=12, background="#FFFFFF")
        canvas.paste(fitted, (box[0], box[1]))
        draw.rectangle((box[0], box[1], box[0] + box[2], box[1] + box[3]), outline="#36454F", width=2)
        draw.text((box[0] + 18, box[1] + 10), f"{index:02d}", font=font(14, True), fill="#FFFFFF")
    draw.text((64, 706), "III   ФАСАДЫ СО ВСЕХ СТОРОН", font=font(15, True), fill="#36454F")
    draw_footer(draw, record, "Фасады и геометрия дома", "#36454F")
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, "PNG", optimize=True)

TITLE_PATTERNS = [
    "Проект №{p} — планы и фасады",
    "Современный дом №{p}: полный обзор",
    "Архитектура дома №{p} без лишнего",
    "Дом №{p}: планировка и пропорции",
    "Проект №{p}: четыре фасада дома",
    "Дом №{p}: визуализация и планы",
]
OPENERS = [
    "В коротком видео собраны внешний вид дома, его планы и фасады.",
    "Архитектурный обзор помогает быстро оценить проект со всех сторон.",
    "Ролик показывает визуализацию, реальную планировку и чертежи фасадов.",
    "Новый формат объединяет главные материалы карточки проекта в одном видео.",
]
MIDDLES = [
    "Проект случайным образом выбран из полного каталога catalog-plans.ru.",
    "Все изображения получены непосредственно из карточки соответствующего проекта.",
    "Планы этажей помогают оценить расположение комнат и общую логику дома.",
    "Четыре фасада дают представление об архитектуре со всех сторон.",
]
CLOSERS = [
    "Откройте проект, чтобы подробно рассмотреть помещения, размеры и фасады.",
    "На сайте доступны все планы, характеристики и состав проектной документации.",
    "Перейдите к карточке дома и оцените характеристики выбранного проекта.",
    "Сохраните вариант и сравните его с другими проектами из каталога.",
]
MOTION_NAMES = ["modern_minimal", "clean_floor_plans", "graphite_facades", "modern_architecture"]


def seo_board(record: ProjectMedia, index: int) -> str:
    boards = [
        "Проекты частных домов",
        "Готовые проекты домов",
        "Планировки загородных домов",
        "Красивые фасады домов",
        "Архитектура частного дома",
        "Дома с планами и фасадами",
    ]
    if record.floors == "1":
        boards += ["Одноэтажные проекты домов"]
    elif record.floors == "2":
        boards += ["Двухэтажные проекты домов"]
    return boards[index % len(boards)]


def keywords(record: ProjectMedia, board: str) -> str:
    values = [
        f"проект дома {record.project}", board, "готовый проект дома",
        "планировка дома", "архитектура дома", "фасады частного дома",
        "поэтажные планы", "фасады дома", "готовый проект дома", "catalog-plans.ru",
    ]
    if record.area:
        values.append(f"дом {record.area} м²")
    if record.material:
        values.append(record.material)
    if record.style:
        values.append(record.style)
    return ", ".join(dict.fromkeys(values))[:500]
'''
source = replace_once(
    source,
    '\n\nif __name__ == "__main__":\n    main()\n',
    seo_overrides + '\n\nif __name__ == "__main__":\n    main()\n',
)

virtual_path = ROOT / "batch44_modern_minimal_video_runtime.py"
namespace = {"__name__": "__main__", "__file__": str(virtual_path)}
exec(compile(source, str(virtual_path), "exec"), namespace)
