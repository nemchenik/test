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

# Use finite still-image inputs and a different sequence for this collection:
# house -> facades -> plan -> house.
source = replace_once(
    source,
    '''        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-loop", "1", "-t", str(STAGE_SECONDS), "-i", str(static_card),
        "-loop", "1", "-t", str(STAGE_SECONDS), "-i", str(plan_slide),
        "-loop", "1", "-t", str(STAGE_SECONDS), "-i", str(facade_slide),
        "-loop", "1", "-t", str(STAGE_SECONDS), "-i", str(static_card),
''',
    '''        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(static_card),
        "-i", str(facade_slide),
        "-i", str(plan_slide),
        "-i", str(static_card),
''',
)
source = replace_once(
    source,
    '''        "-map", "[outv]", "-an",
''',
    '''        "-map", "[outv]", "-t", "8.05", "-an",
''',
)

for old, new in {
    'OUT_DIR = ROOT / "batch36_video_output"': 'OUT_DIR = ROOT / "batch38_video_output"',
    'WORK_DIR = ROOT / "batch36_video_work"': 'WORK_DIR = ROOT / "batch38_video_work"',
    'STATIC_DIR = ASSET_CHECKOUT / "pinterest" / "generated_batch_34_color_static"':
        'STATIC_DIR = WORK_DIR / "house_slides"',
    'VIDEO_DIR = ASSET_CHECKOUT / "pinterest" / "generated_batch_36_house_plan_facade_video"':
        'VIDEO_DIR = ASSET_CHECKOUT / "pinterest" / "generated_batch_38_master_bedroom_video"',
    'CAMPAIGN = "generated_house_plan_facade_video_batch_36"':
        'CAMPAIGN = "generated_master_bedroom_video_batch_38"',
    'START_PIN = 6512': 'START_PIN = 6912',
    'STAGE_SECONDS = 2.0': 'STAGE_SECONDS = 2.4',
    'EXPECTED_DURATION_MIN = 6.35': 'EXPECTED_DURATION_MIN = 7.85',
    'EXPECTED_DURATION_MAX = 6.85': 'EXPECTED_DURATION_MAX = 8.25',
    '"duration_seconds": "6.35-6.85"': '"duration_seconds": "7.85-8.25"',
    'f"pinterest/generated_batch_36_house_plan_facade_video/{record.project}.mp4"':
        'f"pinterest/generated_batch_38_master_bedroom_video/{record.project}.mp4"',
    '"local_validation_batch36.json"': '"local_validation_batch38.json"',
    '"public_validation_batch36.json"': '"public_validation_batch38.json"',
}.items():
    source = replace_once(source, old, new)

old_csv_name = '"catalog_plans_pinterest_house_plan_facade_videos_batch_36_200.csv"'
if source.count(old_csv_name) != 2:
    raise RuntimeError(f"Expected two batch36 CSV references, found {source.count(old_csv_name)}")
source = source.replace(
    old_csv_name,
    '"catalog_plans_pinterest_master_bedroom_videos_batch_38_200.csv"',
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


def master_bedroom_project_ids() -> list[str]:
    result = []
    seen = set()
    for page in range(1, 77):
        suffix = "" if page == 1 else f"?page={page}"
        url = f"https://catalog-plans.ru/catalog/s-master-spalney{suffix}"
        response = old.S.get(url, timeout=60)
        response.raise_for_status()
        values = re.findall(r"href=[\\\"'](?:https://catalog-plans\\.ru)?/catalog/([^\\\"'/?#]+)", response.text, re.I)
        for value in values:
            project = urllib.parse.unquote(value).strip("/")
            if PROJECT_RE.fullmatch(project) and project not in seen:
                seen.add(project)
                result.append(project)
        if len(result) >= 520:
            break
    if len(result) < 200:
        raise RuntimeError(f"Master-bedroom category yielded only {len(result)} project IDs")
    print(f"master-bedroom category projects found: {len(result)}", flush=True)
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
    seed_csv = OUT_DIR / "catalog_plans_pinterest_master_bedroom_videos_batch_38_200.csv"
    if seed_csv.exists():
        with seed_csv.open("r", encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))
        seeded = [Path(urllib.parse.urlsplit(row["Media URL"]).path).stem for row in rows]
        if len(seeded) != 200 or len(set(seeded)) != 200 or not all(PROJECT_RE.fullmatch(item) for item in seeded):
            raise RuntimeError(f"Invalid batch38 seed CSV: {seed_csv}")
        print("using 200 stable project IDs from the batch38 seed CSV", flush=True)
        return seeded

    excluded = published_video_ids()
    all_projects = master_bedroom_project_ids()
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
    canvas = Image.new("RGB", (720, 1080), "#351C26")
    draw = ImageDraw.Draw(canvas)
    draw_header(draw, record.project, "ДОМ С МАСТЕР-СПАЛЬНЕЙ")

    hero = ImageOps.fit(source_image, (636, 610), Image.Resampling.LANCZOS)
    rounded_paste(canvas, hero, (42, 145), radius=26, outline="#D8D0C5")
    draw.text((42, 757), "ДОМ  →  ФАСАДЫ  →  ПРИВАТНАЯ ЗОНА", font=font(18, True), fill="#E4C9AE")

    title_options = [
        f"Дом {record.area} м² с мастер-спальней" if record.area else "Дом с мастер-спальней",
        f"Проект №{record.project}: приватная зона",
        "Мастер-спальня в готовом проекте",
        "Фасады и планировка для семьи",
    ]
    draw_footer(draw, record, title_options[index % len(title_options)], "#C58A56")
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

# Warm editorial palette and copy distinguish this series from batch 37.
for old, new in {
    'Image.new("RGB", (720, 1080), "#08140F")': 'Image.new("RGB", (720, 1080), "#351C26")',
    'Image.new("RGB", (720, 1080), "#0B1512")': 'Image.new("RGB", (720, 1080), "#2A1820")',
    '"РЕАЛЬНЫЕ ПЛАНИРОВКИ ПРОЕКТА"': '"ПЛАНИРОВКА С МАСТЕР-СПАЛЬНЕЙ"',
    '"РЕАЛЬНЫЕ ФАСАДЫ ПРОЕКТА"': '"АРХИТЕКТУРА И ФАСАДЫ ДОМА"',
    '"ДОМ  →  ПЛАНИРОВКИ"': '"ФАСАДЫ  →  ПЛАНИРОВКА"',
    '"ПЛАНИРОВКИ  →  ФАСАДЫ"': '"ПЛАНИРОВКА  →  МАСТЕР-СПАЛЬНЯ"',
    '"Посмотрите, как устроены этажи дома"': '"Найдите приватную зону в планировке"',
    '"Оцените архитектуру дома со всех сторон"': '"Сравните фасады выбранного проекта"',
}.items():
    source = replace_once(source, old, new)
source = source.replace('"#F3EEE5"', '"#FBF0E2"')
source = source.replace('"#1B2A25"', '"#3B1B25"')
source = source.replace('"#D7C9B7"', '"#E4C9AE"')
source = source.replace('"#C86F45"', '"#C58A56"')
source = source.replace('"#B56A45"', '"#B7774B"')

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
        f"[0:v]scale=720:1080,zoompan=z='min(zoom+0.00042,1.035)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={STAGE_FRAMES}:s=720x1080:fps={FPS},setsar=1[v0];"
        f"[1:v]scale=720:1080,zoompan=z='if(eq(on,0),1.035,max(1.0,zoom-0.00036))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={STAGE_FRAMES}:s=720x1080:fps={FPS},setsar=1[v1];"
        f"[2:v]scale=720:1080,zoompan=z='min(zoom+0.00030,1.025)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={STAGE_FRAMES}:s=720x1080:fps={FPS},setsar=1[v2];"
        f"[3:v]scale=720:1080,zoompan=z='1.012+0.005*sin(on/11)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={STAGE_FRAMES}:s=720x1080:fps={FPS},setsar=1[v3];"
        "[v0][v1]xfade=transition=circleopen:duration=0.45:offset=1.95[x1];"
        "[x1][v2]xfade=transition=smoothleft:duration=0.45:offset=3.90[x2];"
        "[x2][v3]xfade=transition=fadeblack:duration=0.45:offset=5.85,"
        "fade=t=in:st=0:d=0.22,fade=t=out:st=7.60:d=0.45,scale=in_range=pc:out_range=tv,format=yuv420p[outv]"
    )
'''
source = replace_once(source, old_filter, new_filter)

seo_overrides = '''

TITLE_PATTERNS = [
    "Проект №{p}: дом с мастер-спальней в видео",
    "Дом №{p}: планировка с приватной спальней",
    "Проект дома №{p}: мастер-спальня и фасады",
    "Дом №{p}: видео планировки для семьи",
    "Проект №{p}: фасады и мастер-спальня",
    "Дом №{p}: приватная зона в планировке",
]
OPENERS = [
    "Видео показывает дом, его фасады и планировку с мастер-спальней.",
    "Ролик начинается с архитектуры дома и переходит к приватной зоне планировки.",
    "В коротком обзоре собраны визуализация, фасады и реальный поэтажный план.",
    "Новый формат помогает оценить дом и расположение мастер-спальни в общей планировке.",
]
MIDDLES = [
    "Проект взят из подборки домов с мастер-спальней на catalog-plans.ru.",
    "Все изображения получены непосредственно из карточки соответствующего проекта.",
    "Мастер-спальня создаёт отдельную приватную зону для владельцев дома.",
    "План этажа помогает сопоставить приватную спальню с остальными помещениями.",
]
CLOSERS = [
    "Откройте проект, чтобы подробно рассмотреть помещения, размеры и фасады.",
    "На сайте доступны все планы, характеристики и состав проектной документации.",
    "Перейдите к карточке дома и проверьте, подходит ли планировка вашей семье.",
    "Сравните этот вариант с другими домами из подборки с мастер-спальней.",
]
MOTION_NAMES = ["master_suite_reveal", "facade_to_private_zone", "family_plan_story", "master_bedroom_focus"]


def seo_board(record: ProjectMedia, index: int) -> str:
    boards = [
        "Проекты домов с мастер-спальней",
        "Планировки домов с мастер-спальней",
        "Мастер-спальня в частном доме",
        "Дома для семьи с планировкой",
        "Фасады домов с планами",
        "Готовые проекты домов с чертежами",
    ]
    if record.floors == "1":
        boards += ["Одноэтажные дома с мастер-спальней"]
    elif record.floors == "2":
        boards += ["Двухэтажные дома с мастер-спальней"]
    return boards[index % len(boards)]


def keywords(record: ProjectMedia, board: str) -> str:
    values = [
        f"проект дома {record.project}", board, "дом с мастер-спальней",
        "планировка с мастер-спальней", "приватная спальня", "гардеробная при спальне",
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

virtual_path = ROOT / "batch38_master_bedroom_video_runtime.py"
namespace = {"__name__": "__main__", "__file__": str(virtual_path)}
exec(compile(source, str(virtual_path), "exec"), namespace)
