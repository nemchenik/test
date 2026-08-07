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

# Keep the ffmpeg fix from batch36 v2: finite zoompan sources plus an explicit
# output duration avoid the infinite process caused by four looped still images.
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
        "-i", str(plan_slide),
        "-i", str(facade_slide),
        "-i", str(static_card),
''',
)
source = replace_once(
    source,
    '''        "-map", "[outv]", "-an",
''',
    '''        "-map", "[outv]", "-t", "6.65", "-an",
''',
)

for old, new in {
    'OUT_DIR = ROOT / "batch36_video_output"': 'OUT_DIR = ROOT / "batch37_video_output"',
    'WORK_DIR = ROOT / "batch36_video_work"': 'WORK_DIR = ROOT / "batch37_video_work"',
    'STATIC_DIR = ASSET_CHECKOUT / "pinterest" / "generated_batch_34_color_static"':
        'STATIC_DIR = WORK_DIR / "house_slides"',
    'VIDEO_DIR = ASSET_CHECKOUT / "pinterest" / "generated_batch_36_house_plan_facade_video"':
        'VIDEO_DIR = ASSET_CHECKOUT / "pinterest" / "generated_batch_37_house_plan_facade_video"',
    'CAMPAIGN = "generated_house_plan_facade_video_batch_36"':
        'CAMPAIGN = "generated_house_plan_facade_video_batch_37"',
    'START_PIN = 6512': 'START_PIN = 6712',
    'f"pinterest/generated_batch_36_house_plan_facade_video/{record.project}.mp4"':
        'f"pinterest/generated_batch_37_house_plan_facade_video/{record.project}.mp4"',
    '"local_validation_batch36.json"': '"local_validation_batch37.json"',
    '"public_validation_batch36.json"': '"public_validation_batch37.json"',
}.items():
    source = replace_once(source, old, new)

old_csv_name = '"catalog_plans_pinterest_house_plan_facade_videos_batch_36_200.csv"'
if source.count(old_csv_name) != 2:
    raise RuntimeError(f"Expected two batch36 CSV references, found {source.count(old_csv_name)}")
source = source.replace(
    old_csv_name,
    '"catalog_plans_pinterest_house_plan_facade_videos_batch_37_200.csv"',
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


def novelty_project_ids() -> list[str]:
    response = old.S.get("https://catalog-plans.ru/catalog/novelty", timeout=60)
    response.raise_for_status()
    values = re.findall(r"href=[\\\"'](?:https://catalog-plans\\.ru)?/catalog/([^\\\"'/?#]+)", response.text, re.I)
    result = []
    seen = set()
    for value in values:
        project = urllib.parse.unquote(value).strip("/")
        if PROJECT_RE.fullmatch(project) and project not in seen:
            seen.add(project)
            result.append(project)
    if not result:
        raise RuntimeError("No project IDs found on the novelty catalog page")
    print(f"novelty projects found: {len(result)}", flush=True)
    return result


def sitemap_project_ids() -> list[str]:
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
    if len(result) < 200:
        raise RuntimeError(f"Sitemap yielded only {len(result)} project IDs")
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
    seed_csv = OUT_DIR / "catalog_plans_pinterest_house_plan_facade_videos_batch_37_200.csv"
    if seed_csv.exists():
        with seed_csv.open("r", encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))
        seeded = [Path(urllib.parse.urlsplit(row["Media URL"]).path).stem for row in rows]
        if len(seeded) != 200 or len(set(seeded)) != 200 or not all(PROJECT_RE.fullmatch(item) for item in seeded):
            raise RuntimeError(f"Invalid batch37 seed CSV: {seed_csv}")
        print("using 200 stable project IDs from the batch37 seed CSV", flush=True)
        return seeded

    excluded = published_video_ids()
    priority = novelty_project_ids()
    all_projects = priority + sitemap_project_ids()
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

house_renderer = '''

def render_house_slide(record: ProjectMedia, index: int, target: Path) -> None:
    data = fetch_image(record.image_url)
    source_image = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
    canvas = Image.new("RGB", (720, 1080), "#08140F")
    draw = ImageDraw.Draw(canvas)
    draw_header(draw, record.project, "ГОТОВЫЙ ПРОЕКТ ДОМА")

    hero = ImageOps.fit(source_image, (636, 610), Image.Resampling.LANCZOS)
    rounded_paste(canvas, hero, (42, 145), radius=26, outline="#D8D0C5")
    draw.text((42, 757), "ДОМ  →  ПЛАНИРОВКИ  →  ФАСАДЫ", font=font(19, True), fill="#D7C9B7")

    title_options = [
        f"Дом {record.area} м²: планы и фасады" if record.area else "Планы и фасады проекта",
        f"Проект №{record.project}: полный обзор",
        "Смотрите дом снаружи и внутри",
        "От визуализации к планам этажей",
    ]
    draw_footer(draw, record, title_options[index % len(title_options)], "#C86F45")
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

virtual_path = ROOT / "batch37_house_plan_facade_video_runtime.py"
namespace = {"__name__": "__main__", "__file__": str(virtual_path)}
exec(compile(source, str(virtual_path), "exec"), namespace)
