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

# Use a new editorial sequence for this collection:
# blueprint -> house -> facade study -> house.
source = replace_once(
    source,
    '''        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-loop", "1", "-t", str(STAGE_SECONDS), "-i", str(static_card),
        "-loop", "1", "-t", str(STAGE_SECONDS), "-i", str(plan_slide),
        "-loop", "1", "-t", str(STAGE_SECONDS), "-i", str(facade_slide),
        "-loop", "1", "-t", str(STAGE_SECONDS), "-i", str(static_card),
''',
    '''        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(plan_slide),
        "-i", str(static_card),
        "-i", str(facade_slide),
        "-i", str(static_card),
''',
)
source = replace_once(
    source,
    '''        "-map", "[outv]", "-an",
''',
    '''        "-map", "[outv]", "-t", "9.20", "-an",
''',
)

for old, new in {
    'OUT_DIR = ROOT / "batch36_video_output"': 'OUT_DIR = ROOT / "batch39_video_output"',
    'WORK_DIR = ROOT / "batch36_video_work"': 'WORK_DIR = ROOT / "batch39_video_work"',
    'STATIC_DIR = ASSET_CHECKOUT / "pinterest" / "generated_batch_34_color_static"':
        'STATIC_DIR = WORK_DIR / "house_slides"',
    'VIDEO_DIR = ASSET_CHECKOUT / "pinterest" / "generated_batch_36_house_plan_facade_video"':
        'VIDEO_DIR = ASSET_CHECKOUT / "pinterest" / "generated_batch_39_panoramic_glazing_video"',
    'CAMPAIGN = "generated_house_plan_facade_video_batch_36"':
        'CAMPAIGN = "generated_panoramic_glazing_video_batch_39"',
    'START_PIN = 6512': 'START_PIN = 7112',
    'STAGE_SECONDS = 2.0': 'STAGE_SECONDS = 2.75',
    'EXPECTED_DURATION_MIN = 6.35': 'EXPECTED_DURATION_MIN = 9.00',
    'EXPECTED_DURATION_MAX = 6.85': 'EXPECTED_DURATION_MAX = 9.40',
    '"duration_seconds": "6.35-6.85"': '"duration_seconds": "9.00-9.40"',
    'f"pinterest/generated_batch_36_house_plan_facade_video/{record.project}.mp4"':
        'f"pinterest/generated_batch_39_panoramic_glazing_video/{record.project}.mp4"',
    '"local_validation_batch36.json"': '"local_validation_batch39.json"',
    '"public_validation_batch36.json"': '"public_validation_batch39.json"',
}.items():
    source = replace_once(source, old, new)

old_csv_name = '"catalog_plans_pinterest_house_plan_facade_videos_batch_36_200.csv"'
if source.count(old_csv_name) != 2:
    raise RuntimeError(f"Expected two batch36 CSV references, found {source.count(old_csv_name)}")
source = source.replace(
    old_csv_name,
    '"catalog_plans_pinterest_panoramic_glazing_videos_batch_39_200.csv"',
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


def panoramic_glazing_project_ids() -> list[str]:
    result = []
    seen = set()
    for page in range(1, 77):
        suffix = "" if page == 1 else f"?page={page}"
        url = f"https://catalog-plans.ru/catalog/s-panoramnym-ostekleniem{suffix}"
        response = old.S.get(url, timeout=60)
        response.raise_for_status()
        values = re.findall(r"href=[\\\"'](?:https://catalog-plans\\.ru)?/catalog/([^\\\"'/?#]+)", response.text, re.I)
        for value in values:
            project = urllib.parse.unquote(value).strip("/")
            if PROJECT_RE.fullmatch(project) and project not in seen:
                seen.add(project)
                result.append(project)
        if len(result) >= 800:
            break
    if len(result) < 200:
        raise RuntimeError(f"Panoramic-glazing category yielded only {len(result)} project IDs")
    print(f"panoramic-glazing category projects found: {len(result)}", flush=True)
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
    seed_csv = OUT_DIR / "catalog_plans_pinterest_panoramic_glazing_videos_batch_39_200.csv"
    if seed_csv.exists():
        with seed_csv.open("r", encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))
        seeded = [Path(urllib.parse.urlsplit(row["Media URL"]).path).stem for row in rows]
        if len(seeded) != 200 or len(set(seeded)) != 200 or not all(PROJECT_RE.fullmatch(item) for item in seeded):
            raise RuntimeError(f"Invalid batch39 seed CSV: {seed_csv}")
        print("using 200 stable project IDs from the batch39 seed CSV", flush=True)
        return seeded

    excluded = published_video_ids()
    all_projects = panoramic_glazing_project_ids()
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
    '''        feature=record.feature,
        plan_urls=plan_urls,
''',
    '''        feature=record.feature,
        image_url=record.image_url,
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
    canvas = Image.new("RGB", (720, 1080), "#F4FAFC")
    draw = ImageDraw.Draw(canvas)
    # Blueprint grid and asymmetric magazine composition.
    for x in range(0, 721, 36):
        draw.line((x, 0, x, 1080), fill="#DDECF2", width=1)
    for y in range(0, 1081, 36):
        draw.line((0, y, 720, y), fill="#DDECF2", width=1)
    draw.rectangle((0, 0, 18, 1080), fill="#00A6C8")
    draw.text((48, 36), "ПАНОРАМНОЕ ОСТЕКЛЕНИЕ", font=font(20, True), fill="#006781")
    draw.text((48, 72), f"ПРОЕКТ {record.project}", font=font(40, True), fill="#092D42")
    draw.rounded_rectangle((498, 38, 678, 86), radius=24, fill="#092D42")
    draw.text((524, 51), "360° ОБЗОР", font=font(16, True), fill="#FFFFFF")

    hero = ImageOps.fit(source_image, (626, 585), Image.Resampling.LANCZOS)
    rounded_paste(canvas, hero, (48, 144), radius=4, outline="#092D42")
    draw.rectangle((48, 729, 674, 737), fill="#00A6C8")
    draw.text((48, 757), "СВЕТ  /  ВИД  /  ПРОСТРАНСТВО", font=font(19, True), fill="#006781")

    title_options = [
        f"Дом {record.area} м² с окнами в пол" if record.area else "Дом с окнами в пол",
        f"Проект №{record.project}: максимум света",
        "Панорамное остекление в архитектуре",
        "Дом, открытый окружающему виду",
    ]
    draw_footer(draw, record, title_options[index % len(title_options)], "#00A6C8")
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
        f"[0:v]scale=720:1080,zoompan=z='if(eq(on,0),1.04,max(1.0,zoom-0.00048))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={STAGE_FRAMES}:s=720x1080:fps={FPS},setsar=1[v0];"
        f"[1:v]scale=720:1080,zoompan=z='min(zoom+0.00052,1.045)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={STAGE_FRAMES}:s=720x1080:fps={FPS},setsar=1[v1];"
        f"[2:v]scale=720:1080,zoompan=z='1.018+0.007*sin(on/12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={STAGE_FRAMES}:s=720x1080:fps={FPS},setsar=1[v2];"
        f"[3:v]scale=720:1080,zoompan=z='if(eq(on,0),1.00,min(1.045,zoom+0.00050))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={STAGE_FRAMES}:s=720x1080:fps={FPS},setsar=1[v3];"
        "[v0][v1]xfade=transition=diagtl:duration=0.60:offset=2.15[x1];"
        "[x1][v2]xfade=transition=hblur:duration=0.60:offset=4.30[x2];"
        "[x2][v3]xfade=transition=pixelize:duration=0.60:offset=6.45,"
        "fade=t=in:st=0:d=0.18,fade=t=out:st=8.75:d=0.45,scale=in_range=pc:out_range=tv,format=yuv420p[outv]"
    )
'''
source = replace_once(source, old_filter, new_filter)

seo_overrides = '''

def draw_blueprint_grid(draw: ImageDraw.ImageDraw) -> None:
    for x in range(0, 721, 36):
        draw.line((x, 0, x, 790), fill="#CDE3EB", width=1)
    for y in range(0, 791, 36):
        draw.line((0, y, 720, y), fill="#CDE3EB", width=1)
    draw.rectangle((0, 0, 18, 1080), fill="#00A6C8")


def render_plan_slide(record: ProjectMedia, plan_paths: list[Path], target: Path) -> None:
    canvas = Image.new("RGB", (720, 1080), "#EAF4F8")
    draw = ImageDraw.Draw(canvas)
    draw_blueprint_grid(draw)
    draw_header(draw, record.project, "ЧЕРТЁЖ / ПЛАНИРОВКА")
    paths = plan_paths[:2]
    boxes = [(48, 150, 624, 570)] if len(paths) == 1 else [(48, 150, 294, 570), (378, 150, 294, 570)]
    for index, (path, box) in enumerate(zip(paths, boxes, strict=False), start=1):
        image = Image.open(path)
        fitted = fit_contain(image, (box[2], box[3]), padding=14, background="#FFFFFF")
        canvas.paste(fitted, (box[0], box[1]))
        draw.rectangle((box[0], box[1], box[0] + box[2], box[1] + box[3]), outline="#18738C", width=2)
        draw.rectangle((box[0] + 12, box[1] + 12, box[0] + 112, box[1] + 44), fill="#00A6C8")
        draw.text((box[0] + 22, box[1] + 19), f"ПЛАН 0{index}", font=font(14, True), fill="#FFFFFF")
    draw.text((48, 750), "01  /  ЧЕРТЁЖ И СВЕТОВЫЕ ЗОНЫ", font=font(19, True), fill="#006781")
    draw_footer(draw, record, "Где окна раскрывают пространство?", "#00A6C8")
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, "PNG", optimize=True)


def render_facade_slide(record: ProjectMedia, facade_paths: list[Path], target: Path) -> None:
    canvas = Image.new("RGB", (720, 1080), "#DCECF2")
    draw = ImageDraw.Draw(canvas)
    draw_blueprint_grid(draw)
    draw_header(draw, record.project, "ОСТЕКЛЁННЫЕ ФАСАДЫ / РАКУРСЫ")
    paths = facade_paths[:4]
    boxes = [(48, 150, 294, 264), (378, 150, 294, 264), (48, 444, 294, 264), (378, 444, 294, 264)]
    if len(paths) == 2:
        boxes = [(48, 165, 624, 250), (48, 445, 624, 250)]
    elif len(paths) == 3:
        boxes = [(48, 150, 294, 264), (378, 150, 294, 264), (213, 444, 294, 264)]
    for index, (path, box) in enumerate(zip(paths, boxes, strict=False), start=1):
        image = Image.open(path)
        fitted = fit_contain(image, (box[2], box[3]), padding=10, background="#FFFFFF")
        canvas.paste(fitted, (box[0], box[1]))
        draw.rectangle((box[0], box[1], box[0] + box[2], box[1] + box[3]), outline="#092D42", width=2)
        draw.rectangle((box[0] + 10, box[1] + 10, box[0] + 82, box[1] + 40), fill="#092D42")
        draw.text((box[0] + 20, box[1] + 16), f"Ф{index:02d}", font=font(13, True), fill="#FFFFFF")
    draw.text((48, 750), "03  /  СРАВНЕНИЕ ОСТЕКЛЕНИЯ", font=font(19, True), fill="#006781")
    draw_footer(draw, record, "Сравните окна на каждом фасаде", "#006781")
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, "PNG", optimize=True)

TITLE_PATTERNS = [
    "Проект №{p}: панорамные окна в видео",
    "Дом №{p}: архитектура с окнами в пол",
    "Проект дома №{p}: свет и панорамный вид",
    "Дом №{p}: фасады с большим остеклением",
    "Проект №{p}: панорамный фасад и планы",
    "Дом №{p}: окна в пол со всех сторон",
]
OPENERS = [
    "Видео показывает проект дома с панорамными окнами, его планы и фасады.",
    "Ролик раскрывает архитектуру дома через свет, большие окна и виды фасадов.",
    "В технологичном обзоре собраны чертежи, визуализация и фасады проекта.",
    "Короткое видео помогает оценить масштаб остекления и связь дома с участком.",
]
MIDDLES = [
    "Проект взят из подборки домов с панорамным остеклением на catalog-plans.ru.",
    "Все изображения получены непосредственно из карточки соответствующего проекта.",
    "Большие окна наполняют интерьер естественным светом и открывают вид на участок.",
    "План этажа помогает понять, какие помещения ориентированы на панорамный фасад.",
]
CLOSERS = [
    "Откройте проект, чтобы подробно рассмотреть помещения, размеры и фасады.",
    "На сайте доступны все планы, характеристики и состав проектной документации.",
    "Перейдите к карточке дома и оцените расположение окон на каждом фасаде.",
    "Сравните этот вариант с другими домами из подборки с панорамным остеклением.",
]
MOTION_NAMES = ["blueprint_to_glass", "panoramic_light_story", "glass_facade_scan", "window_wall_reveal"]


def seo_board(record: ProjectMedia, index: int) -> str:
    boards = [
        "Проекты домов с панорамными окнами",
        "Дома с окнами в пол",
        "Панорамное остекление дома",
        "Современные светлые дома",
        "Фасады домов с большими окнами",
        "Готовые проекты современных домов",
    ]
    if record.floors == "1":
        boards += ["Одноэтажные дома с панорамными окнами"]
    elif record.floors == "2":
        boards += ["Двухэтажные дома с панорамными окнами"]
    return boards[index % len(boards)]


def keywords(record: ProjectMedia, board: str) -> str:
    values = [
        f"проект дома {record.project}", board, "дом с панорамными окнами",
        "панорамное остекление", "окна в пол", "дом с большими окнами",
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

virtual_path = ROOT / "batch39_panoramic_glazing_video_runtime.py"
namespace = {"__name__": "__main__", "__file__": str(virtual_path)}
exec(compile(source, str(virtual_path), "exec"), namespace)
