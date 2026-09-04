from __future__ import annotations

import csv
import io
import json
import math
import os
import re
import shutil
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

os.environ.setdefault("HEAD_SHA", "local")
import audit_generate_v3 as v3
import batch28_generate as b28

ROOT = Path(__file__).parent
OUT = ROOT / "batch31_static_fixed_output"
CARDS = ROOT / "generated_batch_31_static_fixed"
SAMPLES = OUT / "sample_cards"
SRC = OUT / "source_images"
for directory in (OUT, CARDS, SAMPLES, SRC):
    directory.mkdir(parents=True, exist_ok=True)

REPO = os.environ.get("GITHUB_REPOSITORY", "nemchenik/test")
ASSET_BRANCH = os.environ.get("ASSET_BRANCH", "catalog-plans-pinterest-assets")
HEADERS = [
    "Title", "Media URL", "Pinterest board", "Thumbnail",
    "Description", "Link", "Publish date", "Keywords",
]


def clean(value):
    return re.sub(r"\s+", " ", value or "").strip()


def seo_board(record, index):
    try:
        area = float(record.area.replace(",", ".")) if record.area else 0.0
    except Exception:
        area = 0.0
    floors = v3.floor_text(record.floors)
    material = record.material.lower()
    style = record.style.lower()
    feature = record.feature.lower()

    boards = []
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


TITLE_PATTERNS = [
    "Проект дома №{p}: планы, фасады и размеры",
    "Дом №{p}: посмотреть параметры и проект",
    "Проект №{p}: фасады, размеры и планировка",
    "Дом №{p}: открыть характеристики проекта",
    "Проект дома №{p}: оценить метраж и фасад",
    "Дом №{p}: сравнить внешний вид и параметры",
    "Проект №{p}: проверить размеры дома",
    "Дом №{p}: архитектура и основные данные",
]

OPENERS = [
    "На превью показана реальная визуализация дома с catalog-plans.ru.",
    "В карточке использован настоящий фасад проекта из каталога catalog-plans.ru.",
    "На обложке — исходное изображение этого дома с сайта catalog-plans.ru.",
    "Для карточки взята реальная визуализация проекта с catalog-plans.ru.",
    "Пин собран на основе канонического изображения дома из catalog-plans.ru.",
    "На превью размещён реальный фасад проекта из карточки дома на catalog-plans.ru.",
    "В основе этого пина лежит исходная визуализация дома с catalog-plans.ru.",
    "Карточка использует настоящий фасад проекта, опубликованный на catalog-plans.ru.",
]
MIDDLES = [
    "Такой формат помогает быстро сопоставить внешний вид, площадь и параметры дома.",
    "Это удобно для первого отбора проектов ещё до детального просмотра на сайте.",
    "Карточка ускоряет сравнение домов между собой и облегчает выбор в ленте Pinterest.",
    "Так проще понять, стоит ли открывать проект подробнее и сохранять его в доску.",
    "Пин даёт быстрый предпросмотр фасада и ключевых характеристик проекта.",
    "Это хороший способ быстро оценить архитектурный образ и основные цифры проекта.",
    "Такой формат делает выбор проекта более наглядным и быстрым.",
    "Карточка позволяет сразу увидеть проект, номер и базовые параметры дома.",
]
DETAILS = [
    "Такой пин особенно полезен, когда вы сравниваете сразу несколько вариантов.",
    "Это помогает быстрее решить, подходит ли проект по стилю и масштабу.",
    "Для выбора дома под постоянное проживание такой формат очень удобен.",
    "Так проще не потерять интересный проект и вернуться к нему позже.",
    "Если подбираете дом под участок, такой предпросмотр экономит время.",
    "Карточка хорошо работает для быстрого визуального сравнения проектов.",
    "Это удобно, когда вы хотите видеть и фасад, и основные цифры в одном кадре.",
    "Пин рассчитан на быстрый переход к полному описанию проекта на сайте.",
]
CLOSERS = [
    "После перехода на сайт можно изучить планы этажей, фасады, размеры и характеристики.",
    "На странице проекта доступны планировка, фасады, габариты и состав документации.",
    "В карточке проекта на сайте вы увидите планы, фасады, размеры и другие детали.",
    "После перехода откроются планы этажей, архитектурные виды и основные параметры проекта.",
    "На сайте можно проверить планировку, размеры, фасады и дополнительные характеристики.",
    "Карточка проекта содержит планы, фасады, параметры и сведения для осознанного выбора.",
    "На странице проекта вы сможете сравнить параметры, посмотреть планы и оценить фасады.",
    "Дальше на сайте доступен полный набор данных: планы, фасады, размеры и характеристики.",
]


def unique_description(record, index):
    facts = []
    if record.area:
        facts.append(f"площадь {record.area} м²")
    if record.floors:
        facts.append(v3.floor_text(record.floors))
    if record.dimensions:
        facts.append(f"габариты {record.dimensions} м")
    if record.material:
        facts.append(f"материал — {record.material}")
    if record.style:
        facts.append(f"стиль — {record.style}")
    if record.feature:
        facts.append(f"особенность — {record.feature}")
    fact_text = f" Параметры проекта: {'; '.join(facts)}." if facts else ""
    text = (
        f"Проект дома №{record.project}. "
        f"{OPENERS[index % len(OPENERS)]} "
        f"{MIDDLES[index % len(MIDDLES)]}"
        f"{fact_text} "
        f"{DETAILS[index % len(DETAILS)]} "
        f"{CLOSERS[index % len(CLOSERS)]}"
    )
    return clean(text)[:500]


def make_contact_sheet(records):
    tile_w, tile_h, cols = 180, 270, 5
    rows = math.ceil(len(records) / cols)
    sheet = Image.new("RGB", (tile_w * cols, tile_h * rows), "white")
    for index, record in enumerate(records):
        image = Image.open(CARDS / f"{record.project}.jpg")
        image = ImageOps.fit(image, (tile_w, tile_h), Image.Resampling.LANCZOS)
        sheet.paste(image, ((index % cols) * tile_w, (index // cols) * tile_h))
    sheet.save(OUT / "contact_sheet_batch31_static_fixed_200.jpg", "JPEG", quality=88, optimize=True)


def main():
    for directory in (OUT, CARDS, SAMPLES, SRC):
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True, exist_ok=True)

    project_ids = [
        value.strip()
        for value in (ROOT / "projects_candidates.txt").read_text().splitlines()
        if re.fullmatch(r"\d{2}-[A-Za-z0-9]+", value.strip())
    ]

    results = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(b28.old.process, project): project for project in project_ids}
        for future in as_completed(futures):
            project = futures[future]
            try:
                results[project] = future.result()
            except Exception as exc:
                print("SKIP", project, exc, flush=True)
                results[project] = None

    records = []
    used_images = set()
    for project in project_ids:
        record = results.get(project)
        if (
            not record
            or record.image_origin != "og:image"
            or record.white_ratio > 0.55
            or record.image_width < 900
            or not 1.25 <= record.image_width / record.image_height <= 1.85
            or record.image_url in used_images
        ):
            continue
        records.append(v3.normalize_exact_metadata(record))
        used_images.add(record.image_url)
        if len(records) == 200:
            break

    if len(records) != 200:
        raise RuntimeError(f"Only {len(records)} exact house records selected")

    def download(record):
        data = b28.fetch_bytes(record.image_url)
        path = SRC / f"{record.project}.jpg"
        ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB").save(
            path, "JPEG", quality=92, optimize=True
        )
        return record.project

    with ThreadPoolExecutor(max_workers=8) as executor:
        for future in as_completed([executor.submit(download, record) for record in records]):
            future.result()

    intents = {}
    for index, record in enumerate(records):
        target = CARDS / f"{record.project}.jpg"
        intents[record.project] = b28.render_without_button(
            record, index, SRC / f"{record.project}.jpg", target
        )
        with Image.open(target) as check:
            assert check.size == (1000, 1500)
        if index < 8:
            shutil.copy2(target, SAMPLES / target.name)

    rows = []
    audit_rows = []
    for index, record in enumerate(records):
        board = seo_board(record, index)
        pin = 5512 + index
        query = urllib.parse.urlencode({
            "utm_source": "pinterest",
            "utm_medium": "organic",
            "utm_campaign": "generated_house_cards_static_fixed_batch_31",
            "utm_content": f"pin_{pin}_{record.project.lower()}_{intents[record.project]}",
            "utm_term": v3.slug(board),
        })
        media_url = (
            f"https://raw.githubusercontent.com/{REPO}/{ASSET_BRANCH}/"
            f"pinterest/generated_batch_31_static_fixed/{record.project}.jpg"
        )
        rows.append({
            "Title": TITLE_PATTERNS[index % len(TITLE_PATTERNS)].format(p=record.project),
            "Media URL": media_url,
            "Pinterest board": board,
            "Thumbnail": "",
            "Description": unique_description(record, index),
            "Link": f"{record.page_url}?{query}",
            "Publish date": "",
            "Keywords": v3.keywords(record, board),
        })
        audit = asdict(record)
        audit["generated_media_url"] = media_url
        audit["seo_board"] = board
        audit_rows.append(audit)

    assert len(rows) == 200
    assert len({row["Title"] for row in rows}) == 200
    assert len({row["Description"] for row in rows}) == 200
    assert len({row["Media URL"] for row in rows}) == 200
    assert len({row["Link"] for row in rows}) == 200

    csv_name = "catalog_plans_pinterest_house_cards_batch_31_STATIC_FIXED_200.csv"
    csv_path = CARDS / csv_name
    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=HEADERS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    shutil.copy2(csv_path, OUT / csv_name)

    with (OUT / "catalog_plans_house_cards_batch_31_static_audit.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=list(audit_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(audit_rows)

    make_contact_sheet(records)
    (OUT / "summary_batch31_static.json").write_text(
        json.dumps({
            "projects": 200,
            "static_cards": 200,
            "card_size": "1000x1500",
            "dynamic_screenshot_service": False,
            "asset_branch": ASSET_BRANCH,
            "campaign": "generated_house_cards_static_fixed_batch_31",
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    shutil.rmtree(SRC, ignore_errors=True)
    print("SUCCESS 200 static repaired cards", flush=True)


if __name__ == "__main__":
    main()
