#!/usr/bin/env python3
"""Shared renderer for Pinterest cards with a house visualization and floor plans."""

from __future__ import annotations

import csv
import hashlib
import io
import os
from pathlib import Path
import random
import re
import runpy
import textwrap
import time
import urllib.parse

import requests
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FREE_FONT = "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
FREE_FONT_BOLD = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
REPO = "nemchenik/test"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def free_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FREE_FONT_BOLD if bold else FREE_FONT, size)


def fit_font(draw: ImageDraw.ImageDraw, text: str, width: int, start: int, minimum: int, bold: bool = False):
    size = start
    selected = font(size, bold)
    while draw.textbbox((0, 0), text, font=selected)[2] > width and size > minimum:
        size -= 1
        selected = font(size, bold)
    return selected


def fit_free_font(draw: ImageDraw.ImageDraw, text: str, width: int, start: int, minimum: int, bold: bool = False):
    size = start
    selected = free_font(size, bold)
    while draw.textbbox((0, 0), text, font=selected)[2] > width and size > minimum:
        size -= 1
        selected = free_font(size, bold)
    return selected


def cover(image: Image.Image, size: tuple[int, int], focus_y: float = 0.48) -> Image.Image:
    scale = max(size[0] / image.width, size[1] / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = max(0, (resized.width - size[0]) // 2)
    top = max(0, round((resized.height - size[1]) * focus_y))
    return resized.crop((left, top, left + size[0], top + size[1]))


def rounded_paste(canvas: Image.Image, image: Image.Image, box: tuple[int, int, int, int], radius: int, outline: str | None = None, width: int = 0):
    left, top, right, bottom = box
    fitted = cover(image, (right - left, bottom - top))
    mask = Image.new("L", fitted.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, fitted.width, fitted.height), radius=radius, fill=255)
    canvas.paste(fitted, (left, top), mask)
    if outline:
        ImageDraw.Draw(canvas).rounded_rectangle(box, radius=radius, outline=outline, width=width)


def trim_plan(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image).convert("RGB")
    gray = ImageOps.grayscale(image)
    mask = gray.point(lambda value: 255 if value < 246 else 0)
    box = mask.getbbox()
    if not box:
        return image
    left, top, right, bottom = box
    pad_x = max(8, (right - left) // 30)
    pad_y = max(8, (bottom - top) // 30)
    return image.crop((max(0, left - pad_x), max(0, top - pad_y), min(image.width, right + pad_x), min(image.height, bottom + pad_y)))


def contain_plan(image: Image.Image, size: tuple[int, int], background: str = "#FFFFFF") -> Image.Image:
    plan = trim_plan(image)
    plan.thumbnail(size, Image.Resampling.LANCZOS)
    result = Image.new("RGB", size, background)
    result.paste(plan, ((size[0] - plan.width) // 2, (size[1] - plan.height) // 2))
    return result


def fetch_house(url: str) -> Image.Image:
    response = requests.get(url, timeout=40, headers={"User-Agent": "Mozilla/5.0 PinterestPlanCardBot/1.0"})
    response.raise_for_status()
    return ImageOps.exif_transpose(Image.open(io.BytesIO(response.content))).convert("RGB")


def plan_images(work_dir: Path, project: str) -> list[Image.Image]:
    paths = sorted((work_dir / "media" / project).glob("plan_*"))[:2]
    result = []
    for path in paths:
        try:
            result.append(Image.open(path).convert("RGB"))
        except Exception:
            continue
    if not result:
        fallback = work_dir / "plan_slides" / f"{project}.png"
        if fallback.exists():
            result.append(Image.open(fallback).convert("RGB"))
    if not result:
        raise RuntimeError(f"Не найдены планировки проекта {project}")
    return result


def draw_wrapped(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], width: int, selected_font, fill: str, spacing: int = 8, max_lines: int = 3):
    words = text.split()
    lines: list[str] = []
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=selected_font)[2] <= width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    lines = lines[:max_lines]
    draw.multiline_text(xy, "\n".join(lines), font=selected_font, fill=fill, spacing=spacing)


def paste_plan_pair(canvas: Image.Image, plans: list[Image.Image], boxes: list[tuple[int, int, int, int]], border: str, label: str, label_color: str, fill: str = "#FFFFFF", radius: int = 18):
    draw = ImageDraw.Draw(canvas)
    for index, box in enumerate(boxes):
        left, top, right, bottom = box
        draw.rounded_rectangle(box, radius=radius, fill=fill, outline=border, width=3)
        source = plans[min(index, len(plans) - 1)]
        card = contain_plan(source, (right - left - 24, bottom - top - 54), fill)
        canvas.paste(card, (left + 12, top + 42))
        draw.text((left + 18, top + 11), label.format(index + 1), font=font(16, True), fill=label_color)


def facts(record, floor_text):
    return (
        ("ПЛОЩАДЬ", f"{record.area} м²"),
        ("ЭТАЖИ", floor_text(record.floors)),
        ("ГАБАРИТЫ", f"{record.dimensions} м"),
    )


def render_editorial(record, house: Image.Image, plans: list[Image.Image], floor_text) -> Image.Image:
    green, mint, ink, pale, white = "#087F6D", "#32C7A4", "#172622", "#EFF8F5", "#FFFFFF"
    canvas = Image.new("RGB", (1000, 1500), white)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, 1000, 112), fill=green)
    draw.text((42, 25), f"ПРОЕКТ № {record.project}", font=fit_font(draw, f"ПРОЕКТ № {record.project}", 510, 36, 22, True), fill=white)
    draw.text((712, 28), f"{record.area} м²", font=fit_font(draw, f"{record.area} м²", 245, 36, 23, True), fill=white)
    canvas.paste(cover(house, (1000, 560)), (0, 112))
    draw.rectangle((0, 672, 1000, 1500), fill=pale)
    draw.text((44, 704), "ПЛАНИРОВКИ ДОМА", font=font(24, True), fill=green)
    if len(plans) == 1:
        boxes = [(44, 754, 612, 1200)]
    else:
        boxes = [(44, 754, 476, 1200), (492, 754, 924, 1200)]
    paste_plan_pair(canvas, plans, boxes, "#B9D8D0", "ПЛАН ЭТАЖА {}", green, white, 14)
    panel_left = 635 if len(plans) == 1 else 44
    panel_top = 754 if len(plans) == 1 else 1228
    panel_right = 956
    panel_bottom = 1445
    draw.rounded_rectangle((panel_left, panel_top, panel_right, panel_bottom), radius=18, fill=white)
    if len(plans) == 1:
        draw.text((panel_left + 24, panel_top + 25), "КРАТКО О ПРОЕКТЕ", font=font(18, True), fill=green)
        draw_wrapped(draw, "Визуализация и план этажа помогают быстро оценить будущий дом и расположение помещений.", (panel_left + 24, panel_top + 75), panel_right - panel_left - 48, font(19), ink, 8, 5)
        for index, (label, value) in enumerate(facts(record, floor_text)):
            y = panel_top + 230 + index * 78
            draw.text((panel_left + 24, y), label, font=font(14, True), fill=green)
            draw.text((panel_left + 24, y + 27), value, font=fit_font(draw, value, panel_right - panel_left - 48, 21, 15, True), fill=ink)
    else:
        draw.text((panel_left + 22, panel_top + 18), "ВИЗУАЛИЗАЦИЯ И ПЛАНЫ ЭТАЖЕЙ", font=font(17, True), fill=green)
        x = 438
        for label, value in facts(record, floor_text):
            draw.text((x, panel_top + 18), label, font=font(13, True), fill=green)
            draw.text((x, panel_top + 48), value, font=fit_font(draw, value, 150, 19, 14, True), fill=ink)
            x += 170
    draw.text((44, 1460), "catalog-plans.ru", font=font(18, True), fill=green)
    return canvas


def render_blueprint(record, house: Image.Image, plans: list[Image.Image], floor_text) -> Image.Image:
    navy, blue, cyan, paper, white = "#0D2340", "#174B78", "#55C5D8", "#F5F7F8", "#FFFFFF"
    canvas = Image.new("RGB", (1000, 1500), navy)
    draw = ImageDraw.Draw(canvas)
    for x in range(0, 1001, 50):
        draw.line((x, 0, x, 1500), fill="#15304F", width=1)
    for y in range(0, 1501, 50):
        draw.line((0, y, 1000, y), fill="#15304F", width=1)
    draw.text((48, 30), "АРХИТЕКТУРНЫЙ ПРОЕКТ", font=font(18, True), fill=cyan)
    title = f"Дом {record.area} м²"
    draw.text((48, 70), title, font=fit_font(draw, title, 620, 46, 28, True), fill=white)
    draw.text((774, 48), f"№ {record.project}", font=fit_font(draw, f"№ {record.project}", 178, 28, 18, True), fill=white)
    rounded_paste(canvas, house, (48, 145, 952, 675), 22, cyan, 3)
    draw.text((48, 705), "ПЛАНИРОВОЧНЫЕ РЕШЕНИЯ", font=font(22, True), fill=white)
    boxes = [(48, 755, 488, 1208), (512, 755, 952, 1208)] if len(plans) > 1 else [(145, 755, 855, 1208)]
    paste_plan_pair(canvas, plans, boxes, cyan, "ЭТАЖ {}", blue, paper, 12)
    draw.rounded_rectangle((48, 1242, 952, 1432), radius=20, fill=blue, outline=cyan, width=2)
    draw.text((74, 1267), "ГОТОВЫЙ ПРОЕКТ ДЛЯ СТРОИТЕЛЬСТВА", font=font(17, True), fill=cyan)
    x = 74
    for label, value in facts(record, floor_text):
        draw.text((x, 1310), label, font=font(13, True), fill="#A9C7DA")
        draw.text((x, 1340), value, font=fit_font(draw, value, 230, 22, 15, True), fill=white)
        x += 280
    draw.text((48, 1460), "catalog-plans.ru", font=font(18, True), fill=white)
    return canvas


def render_premium(record, house: Image.Image, plans: list[Image.Image], floor_text) -> Image.Image:
    wine, gold, ink, cream, paper = "#6D283B", "#C69A54", "#2D2523", "#F4EBDD", "#FFFDF8"
    canvas = Image.new("RGB", (1000, 1500), cream)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, 1000, 128), fill=wine)
    draw.text((48, 25), "КОЛЛЕКЦИЯ ПРОЕКТОВ ДОМОВ", font=font(17, True), fill="#ECD7B1")
    draw.text((48, 60), f"Проект № {record.project}", font=fit_font(draw, f"Проект № {record.project}", 570, 38, 23, True), fill=paper)
    draw.text((747, 51), f"{record.area} м²", font=fit_font(draw, f"{record.area} м²", 205, 29, 19, True), fill=paper)
    canvas.paste(cover(house, (1000, 560)), (0, 128))
    draw.rectangle((0, 678, 1000, 688), fill=gold)
    draw.text((48, 724), "ПЛАН ДОМА", font=font(23, True), fill=wine)
    draw.text((712, 730), "ПРОДУМАННО ДЛЯ ЖИЗНИ", font=font(14, True), fill=gold)
    boxes = [(48, 770, 488, 1204), (512, 770, 952, 1204)] if len(plans) > 1 else [(165, 770, 835, 1204)]
    paste_plan_pair(canvas, plans, boxes, "#D8C5AA", "ПЛАН {}", wine, paper, 6)
    draw.line((48, 1240, 952, 1240), fill=gold, width=2)
    draw.text((48, 1270), "КРАТКО О ПРОЕКТЕ", font=font(16, True), fill=wine)
    draw_wrapped(draw, "Фасад, планировки и основные параметры проекта — всё необходимое для первого знакомства с домом.", (48, 1304), 500, font(18), ink, 6, 3)
    x = 610
    for label, value in facts(record, floor_text):
        draw.text((x, 1268), label, font=font(12, True), fill=wine)
        draw.text((x, 1295), value, font=fit_font(draw, value, 315, 19, 14, True), fill=ink)
        x = 610
        if label == "ПЛОЩАДЬ":
            x = 780
        elif label == "ЭТАЖИ":
            x = 610
            draw.text((x, 1342), "ГАБАРИТЫ", font=font(12, True), fill=wine)
            draw.text((x, 1369), facts(record, floor_text)[2][1], font=fit_font(draw, facts(record, floor_text)[2][1], 315, 19, 14, True), fill=ink)
            break
    draw.text((48, 1457), "catalog-plans.ru", font=font(18, True), fill=wine)
    return canvas


def render_plans_ocean(record, _house: Image.Image | None, plans: list[Image.Image], floor_text) -> Image.Image:
    navy, teal, seafoam, cream, white = "#1A2332", "#2D8B8B", "#A8DADC", "#F1FAEE", "#FFFFFF"
    canvas = Image.new("RGB", (1000, 1500), cream)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, 1000, 205), fill=navy)
    draw.rectangle((0, 197, 1000, 205), fill=teal)
    draw.text((52, 34), "ОРИГИНАЛЬНАЯ ПЛАНИРОВКА ДОМА", font=font(19, True), fill=seafoam)
    title = f"Проект № {record.project}"
    draw.text((52, 76), title, font=fit_font(draw, title, 585, 44, 27, True), fill=cream)
    draw.text((755, 80), f"{record.area} м²", font=fit_font(draw, f"{record.area} м²", 193, 33, 21, True), fill=cream)
    draw.text((52, 232), "ПЛАНЫ ЭТАЖЕЙ", font=font(21, True), fill=navy)
    boxes = [(52, 278, 486, 980), (514, 278, 948, 980)] if len(plans) > 1 else [(132, 278, 868, 980)]
    paste_plan_pair(canvas, plans, boxes, seafoam, "ЭТАЖ {}", teal, white, 18)
    draw.rounded_rectangle((52, 1018, 948, 1245), radius=25, fill=navy)
    draw.text((82, 1048), "ПЛАНИРОВКА ПРОЕКТА ДОМА", font=font(17, True), fill=seafoam)
    seo = (
        f"Оригинальные планы проекта №{record.project} площадью {record.area} м². "
        "Оцените расположение помещений и сравните этажи перед выбором дома."
    )
    draw_wrapped(draw, seo, (82, 1092), 830, font(22), cream, 9, 4)
    for index, (label, value) in enumerate(facts(record, floor_text)):
        left = 52 + index * 306
        draw.rounded_rectangle((left, 1280, left + 284, 1418), radius=18, fill=white, outline=seafoam, width=3)
        draw.text((left + 22, 1304), label, font=font(14, True), fill=teal)
        draw.text((left + 22, 1347), value, font=fit_font(draw, value, 240, 23, 16, True), fill=navy)
    draw.text((52, 1452), "catalog-plans.ru", font=font(19, True), fill=navy)
    draw.text((700, 1455), "ПЛАНИРОВКИ ДОМОВ", font=font(14, True), fill=teal)
    return canvas


def render_plans_golden(record, _house: Image.Image | None, plans: list[Image.Image], floor_text) -> Image.Image:
    mustard, terracotta, beige, chocolate, paper = "#F4A900", "#C1666B", "#D4B896", "#4A403A", "#FFF9EF"
    canvas = Image.new("RGB", (1000, 1500), chocolate)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, 1000, 220), fill=chocolate)
    draw.rectangle((0, 212, 1000, 220), fill=mustard)
    draw.rounded_rectangle((52, 34, 318, 78), radius=22, fill=terracotta)
    draw.text((82, 43), "ПЛАНИРОВКА ДОМА", font=free_font(18, True), fill=paper)
    title = f"Проект № {record.project}"
    draw.text((52, 100), title, font=fit_font(draw, title, 610, 45, 27, True), fill=paper)
    draw.text((752, 108), f"{record.area} м²", font=fit_font(draw, f"{record.area} м²", 196, 33, 21, True), fill=mustard)
    draw.rectangle((0, 220, 1000, 1010), fill=beige)
    draw.text((52, 248), "ОРИГИНАЛЬНЫЕ ПЛАНЫ ЭТАЖЕЙ", font=free_font(20, True), fill=chocolate)
    boxes = [(52, 296, 486, 970), (514, 296, 948, 970)] if len(plans) > 1 else [(145, 296, 855, 970)]
    paste_plan_pair(canvas, plans, boxes, terracotta, "ПЛАН {}", chocolate, paper, 8)
    draw.rounded_rectangle((52, 1045, 948, 1264), radius=18, fill=paper, outline=mustard, width=3)
    draw.text((80, 1072), "ПРОЕКТ ДОМА С ПЛАНИРОВКОЙ", font=free_font(18, True), fill=terracotta)
    seo = (
        f"Планировка дома №{record.project}: площадь {record.area} м², {floor_text(record.floors)}. "
        "Сохраните планы этажей, чтобы сравнить комнаты и выбрать подходящий проект."
    )
    draw_wrapped(draw, seo, (80, 1114), 830, free_font(22), chocolate, 8, 4)
    for index, (label, value) in enumerate(facts(record, floor_text)):
        left = 52 + index * 306
        draw.rounded_rectangle((left, 1300, left + 284, 1418), radius=16, fill=terracotta if index == 0 else "#5B4D45")
        draw.text((left + 20, 1319), label, font=free_font(14, True), fill=beige)
        draw.text((left + 20, 1355), value, font=fit_font(draw, value, 242, 22, 15, True), fill=paper)
    draw.text((52, 1452), "catalog-plans.ru", font=free_font(19, True), fill=mustard)
    draw.text((616, 1454), "ПРОЕКТЫ С ПЛАНИРОВКОЙ", font=free_font(14, True), fill=beige)
    return canvas


def render_plans_desert_rose(record, _house: Image.Image | None, plans: list[Image.Image], floor_text) -> Image.Image:
    rose, clay, sand, burgundy, paper = "#D4A5A5", "#B87D6D", "#E8D5C4", "#5D2E46", "#FFFDFC"
    canvas = Image.new("RGB", (1000, 1500), sand)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, 1000, 188), fill=burgundy)
    draw.rectangle((0, 188, 1000, 198), fill=clay)
    draw.text((54, 31), "КОЛЛЕКЦИЯ ПЛАНИРОВОК", font=free_font(18, True), fill=rose)
    title = f"Проект дома № {record.project}"
    draw.text((54, 74), title, font=fit_free_font(draw, title, 675, 43, 25, True), fill=paper)
    draw.rounded_rectangle((774, 57, 946, 139), radius=40, fill=rose)
    area = f"{record.area} м²"
    area_font = free_font(25, True)
    area_width = draw.textbbox((0, 0), area, font=area_font)[2]
    draw.text((860 - area_width // 2, 82), area, font=area_font, fill=burgundy)
    draw.text((54, 231), "ОРИГИНАЛЬНЫЕ ПЛАНЫ ЭТАЖЕЙ", font=free_font(21, True), fill=burgundy)
    draw.line((54, 272, 946, 272), fill=clay, width=2)
    boxes = [(54, 305, 486, 1003), (514, 305, 946, 1003)] if len(plans) > 1 else [(146, 305, 854, 1003)]
    paste_plan_pair(canvas, plans, boxes, rose, "ПЛАН ЭТАЖА {}", burgundy, paper, 28)
    draw.rounded_rectangle((54, 1040, 946, 1262), radius=30, fill=paper, outline=rose, width=3)
    draw.text((84, 1068), "ДОМ, В КОТОРОМ ВСЁ НА СВОЁМ МЕСТЕ", font=free_font(17, True), fill=clay)
    seo = (
        f"Планировка проекта №{record.project} площадью {record.area} м². "
        "Изучите расположение комнат и сохраните идею для будущего дома."
    )
    draw_wrapped(draw, seo, (84, 1112), 830, free_font(23), burgundy, 9, 4)
    for index, (label, value) in enumerate(facts(record, floor_text)):
        left = 54 + index * 306
        fill = burgundy if index == 0 else paper
        value_color = paper if index == 0 else burgundy
        draw.rounded_rectangle((left, 1300, left + 280, 1418), radius=26, fill=fill, outline=rose, width=3)
        draw.text((left + 20, 1318), label, font=free_font(13, True), fill=rose if index == 0 else clay)
        draw.text((left + 20, 1352), value, font=fit_free_font(draw, value, 238, 22, 15, True), fill=value_color)
    draw.text((54, 1454), "catalog-plans.ru", font=free_font(19, True), fill=burgundy)
    draw.text((694, 1456), "ПЛАНЫ ДЛЯ ЖИЗНИ", font=free_font(14, True), fill=clay)
    return canvas


def render_plans_tech(record, _house: Image.Image | None, plans: list[Image.Image], floor_text) -> Image.Image:
    blue, cyan, dark, white, panel = "#0066FF", "#00FFFF", "#1E1E1E", "#FFFFFF", "#282A30"
    canvas = Image.new("RGB", (1000, 1500), dark)
    draw = ImageDraw.Draw(canvas)
    for x in range(0, 1001, 40):
        draw.line((x, 0, x, 1500), fill="#262626", width=1)
    for y in range(0, 1501, 40):
        draw.line((0, y, 1000, y), fill="#262626", width=1)
    draw.rectangle((0, 0, 18, 1500), fill=blue)
    draw.text((58, 34), "ТОЧНАЯ ПЛАНИРОВКА ДОМА", font=font(18, True), fill=cyan)
    title = f"ПРОЕКТ № {record.project}"
    draw.text((58, 75), title, font=fit_font(draw, title, 645, 46, 27, True), fill=white)
    draw.rounded_rectangle((760, 52, 944, 139), radius=8, fill=blue)
    area = f"{record.area} м²"
    af = font(25, True)
    aw = draw.textbbox((0, 0), area, font=af)[2]
    draw.text((852 - aw // 2, 80), area, font=af, fill=white)
    draw.line((58, 175, 944, 175), fill=cyan, width=3)
    draw.text((58, 211), "ОРИГИНАЛЬНЫЕ ПЛАНЫ ЭТАЖЕЙ", font=font(20, True), fill=white)
    boxes = [(58, 260, 482, 980), (520, 260, 944, 980)] if len(plans) > 1 else [(148, 260, 854, 980)]
    paste_plan_pair(canvas, plans, boxes, blue, "УРОВЕНЬ {}", blue, white, 6)
    draw.rounded_rectangle((58, 1019, 944, 1249), radius=10, fill=panel, outline=cyan, width=2)
    draw.rectangle((58, 1019, 73, 1249), fill=cyan)
    draw.text((102, 1050), "ПЛАНИРОВОЧНОЕ РЕШЕНИЕ", font=font(17, True), fill=cyan)
    seo = (
        f"Проект №{record.project}: {record.area} м² и {floor_text(record.floors)}. "
        "Сравните планы этажей, оцените логику помещений и сохраните проект."
    )
    draw_wrapped(draw, seo, (102, 1097), 790, font(23), white, 10, 4)
    for index, (label, value) in enumerate(facts(record, floor_text)):
        left = 58 + index * 302
        draw.rectangle((left, 1290, left + 274, 1418), fill=blue if index == 1 else panel, outline=blue, width=3)
        draw.text((left + 18, 1310), label, font=font(13, True), fill=cyan if index != 1 else white)
        draw.text((left + 18, 1350), value, font=fit_font(draw, value, 235, 22, 15, True), fill=white)
    draw.text((58, 1453), "catalog-plans.ru", font=font(19, True), fill=cyan)
    draw.text((688, 1456), "ПРОЕКТЫ И ПЛАНЫ", font=font(14, True), fill=white)
    return canvas


RENDERERS = {
    "editorial": render_editorial,
    "blueprint": render_blueprint,
    "premium": render_premium,
    "plans_ocean": render_plans_ocean,
    "plans_golden": render_plans_golden,
    "plans_desert_rose": render_plans_desert_rose,
    "plans_tech": render_plans_tech,
}


def run_batch(*, batch: int, slug: str, style: str, start_pin: int, board: str = "Проекты частных домов") -> None:
    base = runpy.run_path(str(HERE / "batch53_organic_editorial_static.py"))
    runtime = base["runtime"]
    out_dir = HERE / f"batch{batch}_{slug}_output"
    work_dir = HERE / f"batch{batch}_{slug}_work"
    asset_checkout = Path(os.environ.get("ASSET_CHECKOUT", ROOT / "pinterest_asset_checkout"))
    asset_folder = f"generated_batch_{batch}_{slug}"
    image_dir = asset_checkout / "pinterest" / asset_folder
    csv_path = out_dir / f"catalog_plans_pinterest_{slug}_batch_{batch}_200.csv"
    asset_ref = os.environ.get("ASSET_BRANCH", "catalog-plans-pinterest-assets")
    campaign = f"generated_{slug}_batch_{batch}"

    runtime.update({
        "OUT_DIR": out_dir, "WORK_DIR": work_dir, "MEDIA_DIR": work_dir / "media",
        "PLAN_DIR": work_dir / "plan_slides", "FACADE_DIR": work_dir / "facade_slides",
        "STATIC_DIR": work_dir / "house_slides", "VIDEO_DIR": image_dir,
        "ASSET_CHECKOUT": asset_checkout, "ASSET_BRANCH": asset_ref,
        "CAMPAIGN": campaign, "START_PIN": start_pin,
    })

    def published_project_ids() -> set[str]:
        url = f"https://api.github.com/repos/{REPO}/git/trees/{asset_ref}?recursive=1"
        response = requests.get(url, timeout=60, headers={"User-Agent": "PinterestPlanCardBot/1.0"})
        response.raise_for_status()
        payload = response.json()
        if payload.get("truncated"):
            raise RuntimeError("Дерево GitHub усечено; нельзя надёжно исключить повторы")
        result = set()
        for item in payload.get("tree", []):
            path = item.get("path", "")
            if path.startswith("pinterest/generated_batch_") and Path(path).suffix.lower() in {".jpg", ".mp4"}:
                result.add(Path(path).stem)
        pinterest_root = asset_checkout / "pinterest"
        if pinterest_root.exists():
            for pattern in ("generated_batch_*/*.jpg", "generated_batch_*/*.mp4"):
                result.update(path.stem for path in pinterest_root.glob(pattern))
        return result

    def stable_project_ids():
        if csv_path.exists():
            with csv_path.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            ids = [Path(urllib.parse.urlsplit(row["Media URL"]).path).stem for row in rows]
            if len(ids) == 200 and len(set(ids)) == 200:
                print(f"using 200 stable project IDs from batch {batch} CSV", flush=True)
                return ids
        recovered = sorted(
            path.name for path in (work_dir / "media").glob("*")
            if path.is_dir() and any(path.glob("plan_*")) and runtime["PROJECT_RE"].fullmatch(path.name)
        )
        if len(recovered) == 200:
            print(f"using 200 recovered project IDs from batch {batch} media", flush=True)
            return recovered
        excluded = published_project_ids()
        def read_catalog_page(page: int):
            response = None
            for attempt in range(1, 7):
                try:
                    response = requests.get(
                        "https://catalog-plans.ru/catalog",
                        params={"building_type[]": "жилой дом", "page": page},
                        timeout=45,
                        headers={"User-Agent": "Mozilla/5.0 PinterestPlanCardBot/1.0"},
                    )
                    response.raise_for_status()
                    break
                except requests.RequestException:
                    if attempt == 6:
                        return page, []
                    time.sleep(attempt)
            assert response is not None
            values = re.findall(
                r'href=["\'](?:https://catalog-plans\.ru)?/catalog/([^"\'/?#]+)',
                response.text,
                re.I,
            )
            result = []
            for value in values:
                project = urllib.parse.unquote(value).strip("/")
                if runtime["PROJECT_RE"].fullmatch(project) and project not in result:
                    result.append(project)
            return page, result

        from concurrent.futures import ThreadPoolExecutor, as_completed
        cache_path = HERE / "house_catalog_project_ids_cache.txt"
        if cache_path.exists() and time.time() - cache_path.stat().st_mtime < 86_400:
            house_projects = [line.strip() for line in cache_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        else:
            pages = {}
            with ThreadPoolExecutor(max_workers=6) as executor:
                futures = [executor.submit(read_catalog_page, page) for page in range(1, 251)]
                for future in as_completed(futures):
                    page, values = future.result()
                    pages[page] = values
            house_projects = []
            seen_house = set()
            for page in sorted(pages):
                for project in pages[page]:
                    if project not in seen_house:
                        seen_house.add(project)
                        house_projects.append(project)
            if len(house_projects) < 1000:
                raise RuntimeError(f"Фильтр жилых домов вернул только {len(house_projects)} проектов")
            cache_path.write_text("\n".join(house_projects) + "\n", encoding="utf-8")
        random.Random(f"original-plans-{batch}").shuffle(house_projects)
        print(f"residential catalog projects found: {len(house_projects)}", flush=True)

        candidates = []
        seen = set()
        for project in house_projects:
            if project not in excluded and project not in seen:
                seen.add(project)
                candidates.append(project)
        selected = []
        cache = runtime["PROJECT_CACHE"]
        for offset in range(0, len(candidates), 64):
            chunk = candidates[offset:offset + 64]
            results = {}
            with ThreadPoolExecutor(max_workers=6) as executor:
                futures = {executor.submit(runtime["process_project"], project): project for project in chunk}
                for future in as_completed(futures):
                    project = futures[future]
                    try:
                        results[project] = future.result()
                    except Exception as exc:
                        print(f"SKIP {project}: {exc}", flush=True)
            for project in chunk:
                record = results.get(project)
                if record is not None:
                    cache[project] = record
                    selected.append(project)
                    if len(selected) == 200:
                        print(f"selected 200 new projects; excluded {len(excluded)} published IDs", flush=True)
                        return selected
            print(f"eligible projects selected {len(selected)}/200", flush=True)
        raise RuntimeError(f"Найдено только {len(selected)} подходящих проектов")

    def process_project_with_plans(project: str):
        cache = runtime["PROJECT_CACHE"]
        if project in cache:
            return cache[project]
        record = runtime["old"].process(project)
        if record is None:
            raise RuntimeError(f"metadata not found for {project}")
        record = runtime["v3"].normalize_exact_metadata(record)
        response = runtime["old"].get(record.page_url)
        response.encoding = response.apparent_encoding
        soup = runtime["BeautifulSoup"](response.text, "html.parser")
        meta = soup.select_one('meta[property="og:image"]')
        image_url = urllib.parse.urljoin(record.page_url, meta.get("content", "")) if meta else record.image_url
        plan_urls = runtime["section_urls"](soup, ".media-tile--plan", record.page_url)
        valid_plans = []
        for url in plan_urls:
            try:
                runtime["fetch_image"](url)
                valid_plans.append(url)
            except Exception:
                continue
            if len(valid_plans) == 2:
                break
        if not valid_plans:
            raise RuntimeError(f"no real plan images for {project}")
        result = runtime["ProjectMedia"](
            project=record.project, page_url=record.page_url, area=record.area,
            dimensions=record.dimensions, floors=record.floors, material=record.material,
            style=record.style, feature=record.feature, image_url=image_url,
            plan_urls=valid_plans, facade_urls=[],
        )
        cache[project] = result
        return result

    def download_original_plans(record):
        directory = work_dir / "media" / record.project
        directory.mkdir(parents=True, exist_ok=True)
        paths = []
        for index, url in enumerate(record.plan_urls[:2], 1):
            path = directory / f"plan_{index}.jpg"
            if not path.exists():
                path.write_bytes(runtime["fetch_image"](url))
            paths.append(path)
        return paths, []

    def skip_unused_slide(*_args, **_kwargs):
        return None

    def render(record):
        image_dir.mkdir(parents=True, exist_ok=True)
        house = None if style.startswith("plans_") else fetch_house(record.image_url)
        plans = plan_images(work_dir, record.project)
        canvas = RENDERERS[style](record, house, plans, runtime["floor_text"])
        canvas.save(image_dir / f"{record.project}.jpg", "JPEG", quality=92, optimize=True, progressive=True)

    def validate(records):
        files = []
        for record in records:
            path = image_dir / f"{record.project}.jpg"
            if not path.exists() or path.stat().st_size < 80_000:
                raise RuntimeError(f"Некорректная карточка: {path}")
            with Image.open(path) as image:
                if image.format != "JPEG" or image.size != (1000, 1500):
                    raise RuntimeError(f"Некорректный формат: {path}")
            files.append(path.name)
        return {"images": len(files), "format": "JPEG", "resolution": "1000x1500", "plans": True, "files": files}

    def write_csv(records):
        out_dir.mkdir(parents=True, exist_ok=True)
        fields = ["Title", "Media URL", "Pinterest board", "Thumbnail", "Description", "Link", "Publish date", "Keywords"]
        rows = []
        for offset, record in enumerate(records):
            material = str(record.material).strip()
            rows.append({
                "Title": f"Проект дома №{record.project} площадью {record.area} м² с планировками",
                "Media URL": f"https://raw.githubusercontent.com/{REPO}/{asset_ref}/pinterest/{asset_folder}/{record.project}.jpg",
                "Pinterest board": board, "Thumbnail": "",
                "Description": (
                    f"Проект дома №{record.project}: площадь {record.area} м², {runtime['floor_text'](record.floors)}, "
                    f"габариты {record.dimensions} м, материал стен — {material}. На карточке показаны оригинальные "
                    "планировки этажей. Сохраните планы дома и откройте проект, чтобы узнать подробности и актуальную стоимость."
                    if style.startswith("plans_") else
                    f"Проект дома №{record.project}: площадь {record.area} м², {runtime['floor_text'](record.floors)}, "
                    f"габариты {record.dimensions} м, материал стен — {material}. На карточке показаны визуализация дома "
                    "и планировки этажей. Сохраните идею и откройте проект, чтобы узнать подробности и актуальную стоимость."
                ),
                "Link": (
                    f"{record.page_url}?utm_source=pinterest&utm_medium=organic&utm_campaign={campaign}"
                    f"&utm_content=pin_{start_pin + offset}_{record.project}_plans&utm_term=proekty-domov-s-planirovkami"
                ),
                "Publish date": "",
                "Keywords": (
                    f"проект дома {record.project}, проект дома {record.area} м², планировка дома, планы этажей, "
                    f"готовый проект дома, оригинальная планировка, {material}, catalog-plans.ru"
                    if style.startswith("plans_") else
                    f"проект дома {record.project}, проект дома {record.area} м², планировка дома, планы этажей, "
                    f"готовый проект дома, визуализация дома, {material}, catalog-plans.ru"
                ),
            })
        with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    runtime["published_video_ids"] = published_project_ids
    runtime["project_ids"] = stable_project_ids
    runtime["process_project"] = process_project_with_plans
    runtime["download_project_media"] = download_original_plans
    runtime["render_house_slide"] = skip_unused_slide
    runtime["render_plan_slide"] = skip_unused_slide
    runtime["render_facade_slide"] = skip_unused_slide
    runtime["generate_video"] = render
    runtime["validate_local"] = validate
    runtime["write_csv"] = write_csv
    runtime["main"]()
