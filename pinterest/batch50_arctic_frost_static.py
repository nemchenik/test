#!/usr/bin/env python3
"""Generate 200 Arctic Frost static Pinterest cards from random house projects."""

from __future__ import annotations

import csv
import io
import os
from pathlib import Path
import runpy
import sys

import requests
from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

base = runpy.run_path(str(HERE / "batch49_golden_seo_static.py"))
runtime = base["namespace"]

OUT_DIR = HERE / "batch50_arctic_frost_static_output"
WORK_DIR = HERE / "batch50_arctic_frost_static_work"
ASSET_CHECKOUT = Path(os.environ.get("ASSET_CHECKOUT", ROOT / "pinterest_asset_checkout"))
ASSET_FOLDER = "generated_batch_50_arctic_frost_static"
IMAGE_DIR = ASSET_CHECKOUT / "pinterest" / ASSET_FOLDER
CSV_PATH = OUT_DIR / "catalog_plans_pinterest_arctic_frost_static_batch_50_200.csv"
ASSET_REF = os.environ.get("ASSET_BRANCH", "catalog-plans-pinterest-assets")
CAMPAIGN = "generated_arctic_frost_static_batch_50"
START_PIN = 9312

runtime.update(
    {
        "OUT_DIR": OUT_DIR,
        "WORK_DIR": WORK_DIR,
        "MEDIA_DIR": WORK_DIR / "media",
        "PLAN_DIR": WORK_DIR / "plan_slides",
        "FACADE_DIR": WORK_DIR / "facade_slides",
        "STATIC_DIR": WORK_DIR / "house_slides",
        "VIDEO_DIR": IMAGE_DIR,
        "ASSET_CHECKOUT": ASSET_CHECKOUT,
        "ASSET_BRANCH": ASSET_REF,
        "CAMPAIGN": CAMPAIGN,
        "START_PIN": START_PIN,
    }
)

FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
WHITE = "#FAFAFA"
ICE = "#D4E4F7"
STEEL = "#4A6FA5"
SILVER = "#C0C0C0"
INK = "#15243A"
PALE = "#EEF5FC"


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size)


def cover(image: Image.Image, size: tuple[int, int]):
    scale = max(size[0] / image.width, size[1] / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - size[0]) // 2
    top = (resized.height - size[1]) // 2
    return resized.crop((left, top, left + size[0], top + size[1]))


def fit_font(draw: ImageDraw.ImageDraw, text: str, max_width: int, start: int, minimum: int, bold: bool = False):
    size = start
    current = font(size, bold)
    while draw.textbbox((0, 0), text, font=current)[2] > max_width and size > minimum:
        size -= 1
        current = font(size, bold)
    return current


def fetch_house(url: str):
    response = requests.get(url, timeout=35, headers={"User-Agent": "Mozilla/5.0 PinterestCardBot/1.0"})
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content)).convert("RGB")


def render_card(record):
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGB", (1000, 1500), WHITE)
    draw = ImageDraw.Draw(canvas)

    draw.rectangle((0, 0, 1000, 246), fill=INK)
    draw.rectangle((0, 238, 1000, 246), fill=STEEL)
    draw.rounded_rectangle((64, 44, 275, 91), radius=23, fill=STEEL)
    draw.text((91, 55), "ПРОЕКТ ДОМА", font=font(22, True), fill=WHITE)
    draw.text((64, 112), f"Дом {record.area} м²", font=fit_font(draw, f"Дом {record.area} м²", 650, 62, 40, True), fill=WHITE)
    draw.text((782, 54), f"№ {record.project}", font=fit_font(draw, f"№ {record.project}", 158, 30, 20, True), fill=ICE)
    draw.text((784, 101), "ГОТОВЫЙ ПРОЕКТ", font=font(16, True), fill=SILVER)

    house = cover(fetch_house(record.image_url), (1000, 650))
    canvas.paste(house, (0, 246))
    overlay = Image.new("RGBA", (1000, 650), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle((0, 510, 1000, 650), fill=(21, 36, 58, 188))
    od.text((64, 548), "АРХИТЕКТУРНАЯ ВИЗУАЛИЗАЦИЯ", font=font(22, True), fill=WHITE)
    od.text((64, 591), "Сохраните проект, чтобы вернуться к нему позже", font=font(20), fill=ICE)
    canvas.paste(overlay, (0, 246), overlay)

    draw.rectangle((0, 896, 1000, 1500), fill=PALE)
    draw.text((64, 948), "КЛЮЧЕВЫЕ ХАРАКТЕРИСТИКИ", font=font(20, True), fill=STEEL)
    draw.line((64, 992, 936, 992), fill=SILVER, width=2)

    facts = (
        ("ПЛОЩАДЬ", f"{record.area} м²"),
        ("ЭТАЖНОСТЬ", runtime["floor_text"](record.floors)),
        ("ГАБАРИТЫ", f"{record.dimensions} м"),
    )
    card_width = 272
    for index, (label, value) in enumerate(facts):
        left = 64 + index * 300
        draw.rounded_rectangle((left, 1028, left + card_width, 1215), radius=26, fill=WHITE, outline=ICE, width=3)
        draw.rectangle((left, 1028, left + 10, 1215), fill=STEEL)
        draw.text((left + 34, 1063), label, font=font(17, True), fill=STEEL)
        value_font = fit_font(draw, value, card_width - 56, 31, 20, True)
        draw.text((left + 34, 1120), value, font=value_font, fill=INK)

    material = str(record.material).strip().capitalize()
    draw.text((64, 1261), "МАТЕРИАЛ СТЕН", font=font(17, True), fill=STEEL)
    draw.text((64, 1296), material, font=fit_font(draw, material, 500, 29, 20), fill=INK)
    draw.rounded_rectangle((595, 1250, 936, 1330), radius=40, fill=STEEL)
    draw.text((653, 1275), "СМОТРЕТЬ ПРОЕКТ", font=font(20, True), fill=WHITE)

    draw.line((64, 1375, 936, 1375), fill=SILVER, width=2)
    draw.text((64, 1410), "catalog-plans.ru", font=font(24, True), fill=INK)
    draw.text((674, 1413), "ПРОЕКТЫ ЧАСТНЫХ ДОМОВ", font=font(15, True), fill=STEEL)

    target = IMAGE_DIR / f"{record.project}.jpg"
    canvas.save(target, "JPEG", quality=93, optimize=True, progressive=True)


def validate_cards(records):
    files = []
    for record in records:
        path = IMAGE_DIR / f"{record.project}.jpg"
        if not path.exists() or path.stat().st_size < 80_000:
            raise RuntimeError(f"Некорректная карточка: {path}")
        with Image.open(path) as image:
            if image.size != (1000, 1500) or image.format != "JPEG":
                raise RuntimeError(f"Некорректный формат: {path}")
        files.append(path.name)
    return {"images": len(files), "format": "JPEG", "resolution": "1000x1500", "files": files}


def write_csv(records):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fields = ["Title", "Media URL", "Pinterest board", "Thumbnail", "Description", "Link", "Publish date", "Keywords"]
    rows = []
    for offset, record in enumerate(records):
        pin_number = START_PIN + offset
        media_url = f"https://raw.githubusercontent.com/nemchenik/test/{ASSET_REF}/pinterest/{ASSET_FOLDER}/{record.project}.jpg"
        link = (
            f"{record.page_url}?utm_source=pinterest&utm_medium=organic&utm_campaign={CAMPAIGN}"
            f"&utm_content=pin_{pin_number}_{record.project}_arctic&utm_term=proekty-chastnyh-domov"
        )
        floors = runtime["floor_text"](record.floors)
        material = str(record.material).strip()
        rows.append(
            {
                "Title": f"Проект дома №{record.project} площадью {record.area} м²",
                "Media URL": media_url,
                "Pinterest board": "Проекты частных домов",
                "Thumbnail": "",
                "Description": (
                    f"Готовый проект дома №{record.project} площадью {record.area} м²: {floors}, "
                    f"габариты {record.dimensions} м, материал стен — {material}. "
                    "На карточке показана архитектурная визуализация и основные характеристики. "
                    "Сохраните проект для вдохновения и откройте каталог, чтобы узнать подробности и актуальную стоимость."
                ),
                "Link": link,
                "Publish date": "",
                "Keywords": (
                    f"проект дома {record.project}, проект дома {record.area} м², готовый проект дома, "
                    f"архитектурная визуализация, характеристики дома, частный дом, {material}, catalog-plans.ru"
                ),
            }
        )
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


_base_published_ids = runtime["published_video_ids"]


def published_asset_ids():
    project_ids = set(_base_published_ids())
    pinterest_root = ASSET_CHECKOUT / "pinterest"
    if pinterest_root.exists():
        for path in pinterest_root.glob("generated_batch_*/*.jpg"):
            project_ids.add(path.stem)
    return project_ids


runtime["published_video_ids"] = published_asset_ids
runtime["generate_video"] = render_card
runtime["validate_local"] = validate_cards
runtime["write_csv"] = write_csv


if __name__ == "__main__":
    runtime["main"]()
