#!/usr/bin/env python3
"""Generate 200 random urban-style static Pinterest cards."""

from __future__ import annotations

import csv
import hashlib
import os
from pathlib import Path
import runpy
import sys

from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
base = runpy.run_path(str(HERE / "batch51_chromatic_random_static.py"))
runtime = base["runtime"]
cover = base["cover"]
fetch_house = base["fetch_house"]
fit_font = base["fit_font"]
readable = base["readable"]

OUT_DIR = HERE / "batch52_urban_spectrum_static_output"
WORK_DIR = HERE / "batch52_urban_spectrum_static_work"
ASSET_CHECKOUT = Path(os.environ.get("ASSET_CHECKOUT", ROOT / "pinterest_asset_checkout"))
ASSET_FOLDER = "generated_batch_52_urban_spectrum_static"
IMAGE_DIR = ASSET_CHECKOUT / "pinterest" / ASSET_FOLDER
CSV_PATH = OUT_DIR / "catalog_plans_pinterest_urban_spectrum_static_batch_52_200.csv"
ASSET_REF = os.environ.get("ASSET_BRANCH", "catalog-plans-pinterest-assets")
CAMPAIGN = "generated_urban_spectrum_static_batch_52"
START_PIN = 9712

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

DEJAVU = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
DEJAVU_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FREE = "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
FREE_BOLD = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"


def font(size: int, bold: bool = False, free: bool = False):
    path = FREE_BOLD if free and bold else FREE if free else DEJAVU_BOLD if bold else DEJAVU
    return ImageFont.truetype(path, size)


def seed_for(project: str):
    return int(hashlib.sha256(("urban|" + project).encode()).hexdigest()[:16], 16)


def project_facts(record):
    return (
        ("ПЛОЩАДЬ", f"{record.area} м²"),
        ("ЭТАЖИ", runtime["floor_text"](record.floors)),
        ("РАЗМЕРЫ", f"{record.dimensions} м"),
    )


def layout_tech(record, house):
    blue, cyan, dark, white = "#0066FF", "#00FFFF", "#1E1E1E", "#FFFFFF"
    canvas = Image.new("RGB", (1000, 1500), dark); draw = ImageDraw.Draw(canvas)
    for x in range(0, 1001, 100): draw.line((x, 0, x, 1500), fill="#2A2A2A", width=1)
    for y in range(0, 1501, 100): draw.line((0, y, 1000, y), fill="#2A2A2A", width=1)
    draw.rectangle((0, 0, 18, 1500), fill=cyan)
    draw.text((65, 55), "ПРОЕКТ ЧАСТНОГО ДОМА", font=font(20, True), fill=cyan)
    title = f"Дом {record.area} м²"
    draw.text((65, 105), title, font=fit_font(draw, title, 690, 62, 38, True), fill=white)
    draw.text((790, 65), f"№ {record.project}", font=fit_font(draw, f"№ {record.project}", 165, 29, 18, True), fill=white)
    canvas.paste(cover(house, (870, 680)), (65, 235)); draw = ImageDraw.Draw(canvas)
    draw.rectangle((65, 887, 935, 915), fill=blue); draw.rectangle((65, 887, 380, 915), fill=cyan)
    for index, (label, value) in enumerate(project_facts(record)):
        left = 65 + index * 290
        draw.rectangle((left, 970, left + 260, 1155), fill="#292929", outline=blue, width=3)
        draw.text((left + 22, 1002), label, font=font(15, True), fill=cyan)
        draw.text((left + 22, 1060), value, font=fit_font(draw, value, 215, 27, 18, True), fill=white)
    draw.text((65, 1210), "МАТЕРИАЛ", font=font(16, True), fill=cyan)
    draw.text((65, 1250), str(record.material).capitalize(), font=font(27), fill=white)
    draw.rectangle((595, 1200, 935, 1300), fill=blue)
    draw.text((651, 1234), "СМОТРЕТЬ ПРОЕКТ", font=font(19, True), fill=white)
    draw.text((65, 1400), "catalog-plans.ru", font=font(24, True), fill=white)
    return canvas


def layout_midnight(record, house):
    deep, cosmic, lavender, silver = "#2B1E3E", "#4A4E8F", "#A490C2", "#E6E6FA"
    canvas = Image.new("RGB", (1000, 1500), deep); draw = ImageDraw.Draw(canvas)
    draw.ellipse((700, -180, 1120, 240), fill=cosmic); draw.ellipse((-190, 1080, 300, 1570), fill="#3A2853")
    draw.text((60, 55), "АРХИТЕКТУРНАЯ КОЛЛЕКЦИЯ", font=font(19, True, True), fill=lavender)
    draw.text((60, 105), f"№ {record.project}", font=font(36, True, True), fill=silver)
    canvas.paste(cover(house, (880, 720)), (60, 220)); draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((60, 900, 940, 1390), radius=38, fill=silver)
    title = f"Проект дома {record.area} м²"
    draw.text((95, 945), title, font=fit_font(draw, title, 810, 42, 27, True), fill=deep)
    for index, (label, value) in enumerate(project_facts(record)):
        top = 1030 + index * 88
        draw.text((95, top), label, font=font(15, True, True), fill=cosmic)
        draw.text((420, top - 5), value, font=fit_font(draw, value, 450, 25, 18, True), fill=deep)
    draw.text((95, 1304), str(record.material).capitalize(), font=font(22, False, True), fill=deep)
    draw.rounded_rectangle((602, 1282, 905, 1354), radius=36, fill=cosmic)
    draw.text((655, 1305), "ОТКРЫТЬ ПРОЕКТ", font=font(17, True, True), fill=silver)
    draw.text((60, 1440), "catalog-plans.ru", font=font(22, True, True), fill=silver)
    return canvas


def layout_minimal(record, house):
    charcoal, slate, light, white = "#36454F", "#708090", "#D3D3D3", "#FFFFFF"
    canvas = Image.new("RGB", (1000, 1500), white); draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, 1000, 22), fill=charcoal)
    draw.text((58, 65), "ПРОЕКТ ДОМА", font=font(18, True), fill=slate)
    draw.text((735, 62), f"№ {record.project}", font=fit_font(draw, f"№ {record.project}", 210, 31, 18, True), fill=charcoal)
    title = f"{record.area} м²"
    draw.text((58, 118), title, font=fit_font(draw, title, 650, 78, 48, True), fill=charcoal)
    canvas.paste(cover(house, (1000, 690)), (0, 270)); draw = ImageDraw.Draw(canvas)
    draw.rectangle((58, 1005, 942, 1008), fill=light)
    for index, (label, value) in enumerate(project_facts(record)):
        left = 58 + index * 300
        draw.text((left, 1055), label, font=font(15, True), fill=slate)
        draw.text((left, 1105), value, font=fit_font(draw, value, 260, 28, 18, True), fill=charcoal)
    draw.text((58, 1210), "МАТЕРИАЛ СТЕН", font=font(15, True), fill=slate)
    draw.text((58, 1250), str(record.material).capitalize(), font=font(25), fill=charcoal)
    draw.rectangle((640, 1203, 942, 1300), fill=charcoal)
    draw.text((688, 1236), "СМОТРЕТЬ ПРОЕКТ", font=font(18, True), fill=white)
    draw.text((58, 1410), "catalog-plans.ru", font=font(23, True), fill=charcoal)
    return canvas


def render_card(record):
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    house = fetch_house(record.image_url)
    layouts = (layout_tech, layout_midnight, layout_minimal)
    layouts[seed_for(record.project) % 3](record, house).save(
        IMAGE_DIR / f"{record.project}.jpg", "JPEG", quality=93, optimize=True, progressive=True
    )


def validate_cards(records):
    files = []
    for record in records:
        path = IMAGE_DIR / f"{record.project}.jpg"
        if not path.exists() or path.stat().st_size < 80_000: raise RuntimeError(f"Некорректная карточка: {path}")
        with Image.open(path) as image:
            if image.size != (1000, 1500) or image.format != "JPEG": raise RuntimeError(f"Некорректный формат: {path}")
        files.append(path.name)
    return {"images": len(files), "format": "JPEG", "resolution": "1000x1500", "files": files}


def write_csv(records):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fields = ["Title", "Media URL", "Pinterest board", "Thumbnail", "Description", "Link", "Publish date", "Keywords"]
    rows = []
    for offset, record in enumerate(records):
        material = str(record.material).strip(); pin = START_PIN + offset
        rows.append({
            "Title": f"Проект дома №{record.project} площадью {record.area} м²",
            "Media URL": f"https://raw.githubusercontent.com/nemchenik/test/{ASSET_REF}/pinterest/{ASSET_FOLDER}/{record.project}.jpg",
            "Pinterest board": "Проекты частных домов", "Thumbnail": "",
            "Description": f"Готовый проект дома №{record.project}: площадь {record.area} м², {runtime['floor_text'](record.floors)}, габариты {record.dimensions} м, материал стен — {material}. Сохраните архитектурную визуализацию и откройте каталог, чтобы посмотреть подробности и актуальную стоимость.",
            "Link": f"{record.page_url}?utm_source=pinterest&utm_medium=organic&utm_campaign={CAMPAIGN}&utm_content=pin_{pin}_{record.project}_urban&utm_term=proekty-chastnyh-domov",
            "Publish date": "", "Keywords": f"проект дома {record.project}, проект дома {record.area} м², готовый проект дома, современный дом, характеристики дома, {material}, catalog-plans.ru",
        })
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)


runtime["generate_video"] = render_card
runtime["validate_local"] = validate_cards
runtime["write_csv"] = write_csv

if __name__ == "__main__": runtime["main"]()
