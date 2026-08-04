from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

os.environ.setdefault("HEAD_SHA", "local")
import audit_generate as old
import audit_generate_v3 as v3

ROOT = Path(__file__).parent
OUT_DIR = ROOT / "batch35_video_output"
ASSET_CHECKOUT = Path(os.environ.get("ASSET_CHECKOUT", ROOT / "asset_repo"))
STATIC_DIR = ASSET_CHECKOUT / "pinterest" / "generated_batch_34_color_static"
VIDEO_DIR = ASSET_CHECKOUT / "pinterest" / "generated_batch_35_video"

REPO = os.environ.get("GITHUB_REPOSITORY", "nemchenik/test")
ASSET_BRANCH = os.environ.get("ASSET_BRANCH", "catalog-plans-pinterest-assets")
CAMPAIGN = "generated_house_video_batch_35"
START_PIN = 6312
FPS = 20
DURATION = 5.0
FRAME_COUNT = int(FPS * DURATION)

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CSV_HEADERS = [
    "Title",
    "Media URL",
    "Pinterest board",
    "Thumbnail",
    "Description",
    "Link",
    "Publish date",
    "Keywords",
]

TITLE_PATTERNS = [
    "Проект дома №{p}: короткое видео и планы",
    "Дом №{p}: видео фасада, размеры и проект",
    "Проект №{p}: динамическая карточка дома",
    "Дом №{p}: посмотреть проект в движении",
    "Проект дома №{p}: видео, фасады и размеры",
    "Дом №{p}: короткое видео проекта",
    "Проект №{p}: видео-превью дома",
    "Дом №{p}: фасад в движении и параметры",
]

OPENERS = [
    "Короткое видео мягко приближает карточку и удерживает внимание на фасаде дома.",
    "Видеопревью добавляет плавное движение к карточке проекта и помогает заметить её в ленте.",
    "В ролике используется деликатный зум, чтобы быстрее привлечь взгляд к архитектуре дома.",
    "Карточка оживает за счёт плавного движения и короткого светового акцента.",
    "Динамическая подача помогает остановить прокрутку и рассмотреть проект внимательнее.",
    "Короткая анимация подчёркивает фасад, номер проекта и основные параметры дома.",
    "Видео создаёт лёгкий эффект движения без перегруженных переходов и лишнего шума.",
    "Плавное приближение и световой проход делают проект заметнее в Pinterest-ленте.",
]

MIDDLES = [
    "На основе реальной карточки с catalog-plans.ru удобно быстро оценить масштаб и стиль проекта.",
    "Такой формат подходит для первичного сравнения домов по внешнему виду и ключевым цифрам.",
    "Видео помогает понять, стоит ли открывать проект целиком и сохранять его в подборку.",
    "В одном кадре остаются фасад, номер проекта, площадь и основные характеристики.",
    "Движение привлекает внимание, а спокойный макет сохраняет читаемость информации.",
    "Карточка остаётся полезной для поиска, сравнения и последующего перехода на сайт.",
    "Видео не скрывает параметры проекта и позволяет быстро принять решение о переходе.",
    "Так проще выделить интересный дом среди статичных изображений в результатах поиска.",
]

CLOSERS = [
    "После перехода на сайт можно открыть планы этажей, фасады, размеры и характеристики.",
    "На странице проекта доступны планировка, архитектурные виды, габариты и документация.",
    "Откройте карточку проекта, чтобы изучить планы, фасады и параметры строительства.",
    "На catalog-plans.ru можно подробно проверить планировку и сопоставить дом с участком.",
    "После клика вы увидите полный проект с планами, размерами и дополнительными сведениями.",
    "В каталоге доступны поэтажные решения, фасады и точные характеристики выбранного дома.",
    "Перейдите к проекту, чтобы сравнить габариты, архитектуру и внутреннюю планировку.",
    "На сайте можно оценить проект целиком и перейти к расчёту строительства.",
]

MOTION_NAMES = ["zoom_in", "zoom_out", "pan_right", "float_pulse"]


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def project_ids() -> list[str]:
    if not STATIC_DIR.exists():
        raise RuntimeError(f"Static card directory not found: {STATIC_DIR}")
    ids = sorted(path.stem for path in STATIC_DIR.glob("*.jpg") if re.fullmatch(r"\d{2}-[A-Za-z0-9]+", path.stem))
    if len(ids) != 200:
        raise RuntimeError(f"Expected 200 static cards, found {len(ids)}")
    return ids


def normalize_record(record):
    if record is None:
        return None
    return v3.normalize_exact_metadata(record)


def load_records(ids: list[str]):
    records: dict[str, object] = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(old.process, project): project for project in ids}
        for future in as_completed(futures):
            project = futures[future]
            try:
                records[project] = normalize_record(future.result())
            except Exception as exc:
                raise RuntimeError(f"Metadata failed for {project}: {exc}") from exc
    ordered = [records[project] for project in ids]
    if any(record is None for record in ordered):
        raise RuntimeError("One or more project records are empty")
    return ordered


def seo_board(record, index: int) -> str:
    try:
        area = float(record.area.replace(",", ".")) if record.area else 0.0
    except Exception:
        area = 0.0
    floors = v3.floor_text(record.floors)
    material = record.material.lower()
    style = record.style.lower()
    feature = record.feature.lower()

    boards: list[str] = []
    if area:
        if area <= 100:
            boards += ["Проекты домов до 100 м²", "Маленькие проекты домов"]
        elif area <= 120:
            boards += ["Проекты домов до 120 м²", "Проекты компактных домов"]
        elif area <= 150:
            boards += ["Проекты домов до 150 м²", "Проекты домов 120–150 м²"]
        elif area <= 200:
            boards += ["Проекты домов 150–200 м²", "Проекты семейных домов"]
        elif area <= 300:
            boards += ["Проекты домов 200–300 м²", "Проекты больших домов"]
        else:
            boards += ["Проекты больших коттеджей", "Большие частные дома"]

    if floors == "1 этаж":
        boards += ["Одноэтажные проекты домов", "Проекты одноэтажных коттеджей"]
    elif floors == "2 этажа":
        boards += ["Двухэтажные проекты домов", "Проекты домов 2 этажа"]

    if "газобет" in material:
        boards += ["Проекты домов из газобетона", "Проекты домов из газоблока"]
    elif "кирп" in material or "керамич" in material:
        boards += ["Проекты кирпичных домов", "Проекты домов из кирпича"]
    elif any(token in material for token in ("дерев", "брус", "бревн")):
        boards += ["Проекты деревянных домов", "Деревянные дома с планировкой"]
    elif "каркас" in material:
        boards += ["Каркасные проекты домов", "Проекты каркасных домов"]

    if "современ" in style:
        boards += ["Современные проекты домов", "Проекты домов в современном стиле"]
    elif "европей" in style:
        boards += ["Европейские проекты домов", "Проекты домов в европейском стиле"]
    elif "скандинав" in style:
        boards += ["Скандинавские проекты домов", "Скандинавские дома с планировкой"]
    elif "хай" in style:
        boards += ["Проекты домов в стиле хай-тек", "Дома хай-тек проекты"]
    elif "райта" in style:
        boards += ["Проекты домов в стиле Райта", "Дома в стиле Райта"]

    if "террас" in feature:
        boards += ["Проекты домов с террасой", "Проекты коттеджей с террасой"]
    if "гараж" in feature:
        boards += ["Проекты домов с гаражом", "Проекты коттеджей с гаражом"]
    if "панорам" in feature:
        boards += ["Дома с панорамными окнами", "Проекты домов с панорамными окнами"]
    if "плоск" in feature:
        boards += ["Проекты домов с плоской крышей", "Современные дома с плоской крышей"]
    if "мансард" in feature:
        boards += ["Проекты домов с мансардой", "Дома с мансардой проекты"]

    boards += [
        "Видео проектов домов",
        "Проекты частных домов с планировкой",
        "Проекты домов с размерами",
        "Планы домов и коттеджей",
        "Красивые фасады частных домов",
        "Готовые проекты коттеджей",
        "Проекты загородных домов",
        "Проекты домов для постоянного проживания",
    ]
    boards = list(dict.fromkeys(boards))
    return boards[index % len(boards)]


def facts(record) -> list[str]:
    values: list[str] = []
    if record.area:
        values.append(f"площадь {record.area} м²")
    if record.floors:
        values.append(v3.floor_text(record.floors))
    if record.dimensions:
        values.append(f"габариты {record.dimensions} м")
    if record.material:
        values.append(f"материал — {record.material}")
    if record.style:
        values.append(f"стиль — {record.style}")
    if record.feature:
        values.append(f"особенность — {record.feature}")
    return values


def description(record, index: int) -> str:
    record_facts = facts(record)
    fact_text = f" Параметры проекта: {'; '.join(record_facts)}." if record_facts else ""
    text = (
        f"Проект дома №{record.project}. "
        f"{OPENERS[index % len(OPENERS)]} "
        f"{MIDDLES[index % len(MIDDLES)]}"
        f"{fact_text} "
        f"{CLOSERS[index % len(CLOSERS)]}"
    )
    return clean(text)[:500]


def filter_for(index: int) -> str:
    style = index % 4
    if style == 0:
        zoom = "z='min(zoom+0.00065,1.065)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)-on*0.12'"
    elif style == 1:
        zoom = "z='if(eq(on,0),1.065,max(1.0,zoom-0.00065))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)+on*0.10'"
    elif style == 2:
        zoom = "z='1.055':x='(iw-iw/zoom)*(on/99)':y='ih/2-(ih/zoom/2)'"
    else:
        zoom = "z='1.025+0.012*sin(on/13)':x='iw/2-(iw/zoom/2)+5*sin(on/11)':y='ih/2-(ih/zoom/2)+4*cos(on/14)'"

    drawtext = (
        f"drawtext=fontfile={FONT_BOLD}:text='СМОТРЕТЬ ПРОЕКТ  →':"
        "fontcolor=white:fontsize=24:box=1:boxcolor=black@0.38:boxborderw=12:"
        "x='w-tw-28-6*sin(2*PI*t)':y='h-th-34':"
        "alpha='if(lt(t,0.4),t/0.4,if(gt(t,4.6),(5-t)/0.4,1))'"
    )
    return (
        f"zoompan={zoom}:d={FRAME_COUNT}:s=720x1080:fps={FPS},"
        "drawbox=x='-90+(w+180)*t/5':y=0:w=80:h=h:color=white@0.055:t=fill,"
        f"{drawtext},"
        "fade=t=in:st=0:d=0.25,fade=t=out:st=4.55:d=0.45,format=yuv420p"
    )


def generate_one(project: str, index: int) -> tuple[str, int]:
    source = STATIC_DIR / f"{project}.jpg"
    target = VIDEO_DIR / f"{project}.mp4"
    target.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-loop",
        "1",
        "-framerate",
        "1",
        "-i",
        str(source),
        "-vf",
        filter_for(index),
        "-frames:v",
        str(FRAME_COUNT),
        "-an",
        "-c:v",
        "libx264",
        "-profile:v",
        "high",
        "-level",
        "4.0",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "veryfast",
        "-crf",
        "30",
        "-movflags",
        "+faststart",
        "-threads",
        "1",
        str(target),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed for {project}: {result.stderr[-1200:]}")
    if target.stat().st_size < 35_000:
        raise RuntimeError(f"Video too small for {project}: {target.stat().st_size}")
    return project, target.stat().st_size


def ffprobe(path: Path) -> dict:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=codec_name,width,height,pix_fmt,duration:format=duration,size",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    stream = data["streams"][0]
    duration = float(stream.get("duration") or data["format"]["duration"])
    return {
        "codec": stream["codec_name"],
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "pix_fmt": stream["pix_fmt"],
        "duration": duration,
        "size": int(data["format"]["size"]),
    }


def validate_local(ids: list[str]) -> list[dict]:
    report = []
    for project in ids:
        path = VIDEO_DIR / f"{project}.mp4"
        info = ffprobe(path)
        if info["codec"] != "h264":
            raise RuntimeError(f"Unexpected codec for {project}: {info}")
        if (info["width"], info["height"]) != (720, 1080):
            raise RuntimeError(f"Unexpected size for {project}: {info}")
        if info["pix_fmt"] != "yuv420p":
            raise RuntimeError(f"Unexpected pixel format for {project}: {info}")
        if not 4.8 <= info["duration"] <= 5.2:
            raise RuntimeError(f"Unexpected duration for {project}: {info}")
        info["project"] = project
        info["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        report.append(info)
    return report


def write_csv(records, ids: list[str]) -> Path:
    rows = []
    for index, (record, project) in enumerate(zip(records, ids, strict=True)):
        board = seo_board(record, index)
        pin = START_PIN + index
        query = urllib.parse.urlencode(
            {
                "utm_source": "pinterest",
                "utm_medium": "organic",
                "utm_campaign": CAMPAIGN,
                "utm_content": f"pin_{pin}_{project.lower()}_{MOTION_NAMES[index % 4]}",
                "utm_term": v3.slug(board),
            }
        )
        media_url = (
            f"https://raw.githubusercontent.com/{REPO}/{ASSET_BRANCH}/"
            f"pinterest/generated_batch_35_video/{project}.mp4"
        )
        rows.append(
            {
                "Title": TITLE_PATTERNS[index % len(TITLE_PATTERNS)].format(p=project),
                "Media URL": media_url,
                "Pinterest board": board,
                "Thumbnail": "00:01",
                "Description": description(record, index),
                "Link": f"{record.page_url}?{query}",
                "Publish date": "",
                "Keywords": v3.keywords(record, board) + ", видео проекта дома, короткое видео дома",
            }
        )

    if len(rows) != 200:
        raise RuntimeError(f"Expected 200 CSV rows, got {len(rows)}")
    if len({row["Title"] for row in rows}) != 200:
        raise RuntimeError("Titles are not unique")
    if len({row["Description"] for row in rows}) != 200:
        raise RuntimeError("Descriptions are not unique")
    if len({row["Media URL"] for row in rows}) != 200:
        raise RuntimeError("Media URLs are not unique")
    if not all(row["Media URL"].endswith(".mp4") for row in rows):
        raise RuntimeError("One or more media URLs do not end with .mp4")
    if not all(len(row["Title"]) <= 100 for row in rows):
        raise RuntimeError("A title exceeds 100 characters")
    if not all(len(row["Description"]) <= 500 for row in rows):
        raise RuntimeError("A description exceeds 500 characters")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "catalog_plans_pinterest_house_videos_batch_35_200.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_HEADERS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return csv_path


def generate() -> None:
    ids = project_ids()
    records = load_records(ids)
    if VIDEO_DIR.exists():
        shutil.rmtree(VIDEO_DIR)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(generate_one, project, index): project
            for index, project in enumerate(ids)
        }
        for count, future in enumerate(as_completed(futures), start=1):
            future.result()
            if count % 20 == 0:
                print(f"generated {count}/200", flush=True)

    local_report = validate_local(ids)
    csv_path = write_csv(records, ids)
    (OUT_DIR / "local_video_validation.json").write_text(
        json.dumps(
            {
                "videos": 200,
                "resolution": "720x1080",
                "aspect_ratio": "2:3",
                "duration_seconds": 5,
                "fps": FPS,
                "codec": "H.264",
                "audio": False,
                "motion_styles": MOTION_NAMES,
                "files": local_report,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"SUCCESS generated {len(ids)} videos and {csv_path}", flush=True)


def verify_remote_one(row: dict[str, str], session: requests.Session) -> dict:
    url = row["Media URL"]
    project = Path(urllib.parse.urlsplit(url).path).stem
    local = VIDEO_DIR / f"{project}.mp4"
    expected = hashlib.sha256(local.read_bytes()).hexdigest()
    error: Exception | None = None
    for attempt in range(8):
        try:
            response = session.get(url, timeout=45, headers={"Cache-Control": "no-cache"})
            response.raise_for_status()
            data = response.content
            if len(data) < 35_000:
                raise RuntimeError(f"remote file too small: {len(data)}")
            if b"ftyp" not in data[:32]:
                raise RuntimeError("MP4 ftyp signature not found")
            actual = hashlib.sha256(data).hexdigest()
            if actual != expected:
                raise RuntimeError("remote SHA256 mismatch")
            return {"project": project, "url": url, "sha256": actual, "bytes": len(data)}
        except Exception as exc:
            error = exc
            time.sleep(2 + attempt * 2)
    raise RuntimeError(f"Remote verification failed for {project}: {error}")


def verify_public() -> None:
    csv_path = OUT_DIR / "catalog_plans_pinterest_house_videos_batch_35_200.csv"
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    if len(rows) != 200:
        raise RuntimeError(f"Expected 200 CSV rows, got {len(rows)}")

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 CatalogPlansPinterestVideoVerifier/1.0"})
    verified = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(verify_remote_one, row, session) for row in rows]
        for count, future in enumerate(as_completed(futures), start=1):
            verified.append(future.result())
            if count % 20 == 0:
                print(f"verified {count}/200", flush=True)

    (OUT_DIR / "public_video_verification.json").write_text(
        json.dumps(
            {
                "total": 200,
                "verified": len(verified),
                "all_public_urls_http_200": len(verified) == 200,
                "all_remote_sha256_match_local": len(verified) == 200,
                "files": sorted(verified, key=lambda item: item["project"]),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("SUCCESS all 200 public MP4 URLs verified", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-public", action="store_true")
    args = parser.parse_args()
    if args.verify_public:
        verify_public()
    else:
        generate()


if __name__ == "__main__":
    main()
