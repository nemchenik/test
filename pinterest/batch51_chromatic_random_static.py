#!/usr/bin/env python3
"""Generate 200 readable static Pinterest cards with unique deterministic colors."""

from __future__ import annotations

import colorsys
import csv
import hashlib
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
base = runpy.run_path(str(HERE / "batch50_arctic_frost_static.py"))
runtime = base["runtime"]

OUT_DIR = HERE / "batch51_chromatic_random_static_output"
WORK_DIR = HERE / "batch51_chromatic_random_static_work"
ASSET_CHECKOUT = Path(os.environ.get("ASSET_CHECKOUT", ROOT / "pinterest_asset_checkout"))
ASSET_FOLDER = "generated_batch_51_chromatic_random_static"
IMAGE_DIR = ASSET_CHECKOUT / "pinterest" / ASSET_FOLDER
CSV_PATH = OUT_DIR / "catalog_plans_pinterest_chromatic_random_static_batch_51_200.csv"
ASSET_REF = os.environ.get("ASSET_BRANCH", "catalog-plans-pinterest-assets")
CAMPAIGN = "generated_chromatic_random_static_batch_51"
START_PIN = 9512

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
WHITE = "#FFFFFF"
NEAR_WHITE = "#FAFAFA"
INK = "#141820"


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size)


def hex_color(hue: float, saturation: float, lightness: float):
    red, green, blue = colorsys.hls_to_rgb(hue / 360, lightness / 100, saturation / 100)
    return "#%02x%02x%02x" % (round(red * 255), round(green * 255), round(blue * 255))


def palette(project: str):
    seed = int(hashlib.sha256(project.encode()).hexdigest()[:16], 16)
    hue = seed % 360
    primary = hex_color(hue, 55 + seed % 24, 24 + (seed // 7) % 11)
    accent_hue = (hue + 150 + (seed // 13) % 61) % 360
    accent = hex_color(accent_hue, 65 + (seed // 17) % 24, 48 + (seed // 19) % 15)
    surface = hex_color(hue, 18 + (seed // 23) % 11, 94 + (seed // 29) % 4)
    secondary = hex_color((hue + 28) % 360, 30 + (seed // 31) % 19, 72 + (seed // 37) % 13)
    return seed, primary, accent, surface, secondary


def rgb(value: str):
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def luminance(value: str):
    channels = []
    for channel in rgb(value):
        normalized = channel / 255
        channels.append(normalized / 12.92 if normalized <= 0.04045 else ((normalized + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast(left: str, right: str):
    first, second = sorted((luminance(left), luminance(right)), reverse=True)
    return (first + 0.05) / (second + 0.05)


def readable(background: str):
    return WHITE if contrast(background, WHITE) >= contrast(background, INK) else INK


def fit_font(draw: ImageDraw.ImageDraw, text: str, width: int, start: int, minimum: int, bold: bool = False):
    size = start
    current = font(size, bold)
    while draw.textbbox((0, 0), text, font=current)[2] > width and size > minimum:
        size -= 1
        current = font(size, bold)
    return current


def fetch_house(url: str):
    response = requests.get(url, timeout=35, headers={"User-Agent": "Mozilla/5.0 PinterestCardBot/1.0"})
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content)).convert("RGB")


def cover(image: Image.Image, size: tuple[int, int]):
    scale = max(size[0] / image.width, size[1] / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - size[0]) // 2
    top = (resized.height - size[1]) // 2
    return resized.crop((left, top, left + size[0], top + size[1]))


def facts(record):
    return (
        ("ПЛОЩАДЬ", f"{record.area} м²"),
        ("ЭТАЖНОСТЬ", runtime["floor_text"](record.floors)),
        ("ГАБАРИТЫ", f"{record.dimensions} м"),
    )


def fact_card(draw, box, label, value, background, accent, text_color=None):
    left, top, right, bottom = box
    draw.rounded_rectangle(box, radius=24, fill=background)
    draw.rectangle((left, top, left + 9, bottom), fill=accent)
    color = text_color or readable(background)
    draw.text((left + 30, top + 25), label, font=font(16, True), fill=color)
    draw.text((left + 30, top + 70), value, font=fit_font(draw, value, right - left - 50, 29, 19, True), fill=color)


def layout_editorial(record, house, primary, accent, surface, secondary):
    canvas = cover(house, (1000, 1500))
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0)); od = ImageDraw.Draw(overlay)
    od.rectangle((0, 0, 1000, 320), fill=(*rgb(primary), 225))
    od.rounded_rectangle((54, 955, 946, 1450), radius=36, fill=(*rgb(surface), 245))
    canvas.paste(overlay, (0, 0), overlay); draw = ImageDraw.Draw(canvas)
    title_color = readable(primary)
    draw.text((60, 54), "ГОТОВЫЙ ПРОЕКТ ДОМА", font=font(21, True), fill=title_color)
    title = f"Дом {record.area} м²"
    draw.text((60, 112), title, font=fit_font(draw, title, 650, 62, 38, True), fill=title_color)
    draw.text((758, 64), f"№ {record.project}", font=fit_font(draw, f"№ {record.project}", 185, 31, 19, True), fill=title_color)
    draw.text((88, 990), "ХАРАКТЕРИСТИКИ ПРОЕКТА", font=font(20, True), fill=primary)
    for index, (label, value) in enumerate(facts(record)):
        fact_card(draw, (88 + index * 278, 1040, 342 + index * 278, 1205), label, value, WHITE, accent, INK)
    draw.text((88, 1255), "МАТЕРИАЛ СТЕН", font=font(16, True), fill=primary)
    draw.text((88, 1290), str(record.material).capitalize(), font=font(26), fill=INK)
    draw.rounded_rectangle((574, 1248, 912, 1330), radius=40, fill=accent)
    draw.text((625, 1273), "СМОТРЕТЬ ПРОЕКТ", font=font(19, True), fill=readable(accent))
    draw.text((88, 1383), "catalog-plans.ru", font=font(22, True), fill=primary)
    return canvas


def layout_split(record, house, primary, accent, surface, secondary):
    canvas = Image.new("RGB", (1000, 1500), primary); draw = ImageDraw.Draw(canvas)
    canvas.paste(cover(house, (1000, 735)), (0, 0)); title_color = readable(primary)
    draw.rectangle((0, 720, 1000, 1500), fill=primary)
    draw.rectangle((64, 770, 186, 782), fill=accent)
    draw.text((64, 815), f"ПРОЕКТ № {record.project}", font=font(20, True), fill=title_color)
    title = f"Дом площадью {record.area} м²"
    draw.text((64, 865), title, font=fit_font(draw, title, 872, 48, 31, True), fill=title_color)
    for index, (label, value) in enumerate(facts(record)):
        top = 970 + index * 113
        draw.text((64, top), label, font=font(16, True), fill=secondary)
        draw.text((348, top - 6), value, font=fit_font(draw, value, 560, 28, 19, True), fill=title_color)
        draw.line((64, top + 48, 936, top + 48), fill=secondary, width=2)
    draw.text((64, 1327), str(record.material).capitalize(), font=font(22), fill=title_color)
    draw.rounded_rectangle((608, 1300, 936, 1380), radius=40, fill=accent)
    draw.text((656, 1325), "ОТКРЫТЬ ПРОЕКТ", font=font(18, True), fill=readable(accent))
    draw.text((64, 1433), "catalog-plans.ru", font=font(21, True), fill=title_color)
    return canvas


def layout_gallery(record, house, primary, accent, surface, secondary):
    canvas = Image.new("RGB", (1000, 1500), surface); draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, 1000, 205), fill=primary); title_color = readable(primary)
    draw.text((60, 45), "ПРОЕКТ ЧАСТНОГО ДОМА", font=font(19, True), fill=title_color)
    draw.text((60, 92), f"№ {record.project}", font=font(42, True), fill=title_color)
    draw.rounded_rectangle((60, 245, 940, 865), radius=30, fill=WHITE, outline=secondary, width=5)
    canvas.paste(cover(house, (836, 576)), (82, 267)); draw = ImageDraw.Draw(canvas)
    title = f"Проект дома {record.area} м²"
    draw.text((60, 915), title, font=fit_font(draw, title, 880, 43, 29, True), fill=primary)
    for index, (label, value) in enumerate(facts(record)):
        fact_card(draw, (60 + index * 298, 1000, 338 + index * 298, 1170), label, value, WHITE, primary, INK)
    draw.rounded_rectangle((60, 1225, 940, 1340), radius=28, fill=accent)
    draw.text((91, 1260), str(record.material).capitalize(), font=font(23, True), fill=readable(accent))
    draw.text((660, 1262), "СМОТРЕТЬ →", font=font(21, True), fill=readable(accent))
    draw.text((60, 1405), "catalog-plans.ru", font=font(23, True), fill=primary)
    return canvas


def layout_poster(record, house, primary, accent, surface, secondary):
    canvas = Image.new("RGB", (1000, 1500), primary); draw = ImageDraw.Draw(canvas); title_color = readable(primary)
    draw.text((52, 42), "ГОТОВЫЙ ПРОЕКТ", font=font(18, True), fill=secondary)
    draw.text((52, 82), str(record.area), font=fit_font(draw, str(record.area), 560, 105, 64, True), fill=title_color)
    draw.text((58, 187), "М²", font=font(29, True), fill=accent)
    draw.text((736, 70), f"№ {record.project}", font=fit_font(draw, f"№ {record.project}", 210, 30, 19, True), fill=title_color)
    canvas.paste(cover(house, (840, 690)), (160, 275)); draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 910, 1000, 1500), fill=surface)
    draw.text((58, 955), "ДОМ ДЛЯ СТРОИТЕЛЬСТВА", font=font(21, True), fill=primary)
    for index, (label, value) in enumerate(facts(record)[1:]):
        fact_card(draw, (58 + index * 445, 1012, 470 + index * 445, 1178), label, value, WHITE, accent, INK)
    draw.text((58, 1230), "МАТЕРИАЛ", font=font(16, True), fill=primary)
    draw.text((58, 1265), str(record.material).capitalize(), font=font(27), fill=INK)
    draw.rounded_rectangle((585, 1227, 942, 1320), radius=46, fill=primary)
    draw.text((640, 1257), "СМОТРЕТЬ ПРОЕКТ", font=font(19, True), fill=readable(primary))
    draw.line((58, 1380, 942, 1380), fill=secondary, width=3)
    draw.text((58, 1420), "catalog-plans.ru", font=font(23, True), fill=primary)
    return canvas


def render_card(record):
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    seed, primary, accent, surface, secondary = palette(record.project)
    house = fetch_house(record.image_url)
    layouts = (layout_editorial, layout_split, layout_gallery, layout_poster)
    canvas = layouts[seed % len(layouts)](record, house, primary, accent, surface, secondary)
    canvas.save(IMAGE_DIR / f"{record.project}.jpg", "JPEG", quality=93, optimize=True, progressive=True)


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
        material = str(record.material).strip()
        rows.append(
            {
                "Title": f"Проект дома №{record.project} площадью {record.area} м²",
                "Media URL": f"https://raw.githubusercontent.com/nemchenik/test/{ASSET_REF}/pinterest/{ASSET_FOLDER}/{record.project}.jpg",
                "Pinterest board": "Проекты частных домов",
                "Thumbnail": "",
                "Description": (
                    f"Готовый проект дома №{record.project} площадью {record.area} м²: "
                    f"{runtime['floor_text'](record.floors)}, габариты {record.dimensions} м, материал стен — {material}. "
                    "Архитектурная визуализация и ключевые характеристики собраны на одной карточке. "
                    "Сохраните проект и откройте каталог, чтобы посмотреть подробности и актуальную стоимость."
                ),
                "Link": (
                    f"{record.page_url}?utm_source=pinterest&utm_medium=organic&utm_campaign={CAMPAIGN}"
                    f"&utm_content=pin_{pin_number}_{record.project}_chromatic&utm_term=proekty-chastnyh-domov"
                ),
                "Publish date": "",
                "Keywords": (
                    f"проект дома {record.project}, проект дома {record.area} м², готовый проект дома, "
                    f"визуализация дома, характеристики дома, частный дом, {material}, catalog-plans.ru"
                ),
            }
        )
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


runtime["generate_video"] = render_card
runtime["validate_local"] = validate_cards
runtime["write_csv"] = write_csv


if __name__ == "__main__":
    runtime["main"]()
