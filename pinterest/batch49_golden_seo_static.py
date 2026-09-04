#!/usr/bin/env python3
"""Batch 49: Golden Hour static Pinterest cards with SEO copy and facts."""

from pathlib import Path
import csv
import sys
import types

from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
base_path = HERE / "batch48_premium_choice_video.py"
outer = base_path.read_text(encoding="utf-8")
outer = outer.replace(
    'exec(compile(source, str(Path(__file__).with_name("batch48_premium_choice_runtime.py")), "exec"), namespace)',
    "captured_outer = source",
)
capture = {"__file__": str(base_path), "__name__": "batch49_capture"}
exec(compile(outer, str(base_path), "exec"), capture)

stage_two = capture["captured_outer"].replace(
    'exec(compile(source, str(virtual_path), "exec"), namespace)',
    "captured_runtime = source",
)
capture_two = {"__file__": str(HERE / "batch49_outer.py"), "__name__": "batch49_capture"}
exec(compile(stage_two, str(HERE / "batch49_outer.py"), "exec"), capture_two)

runtime = capture_two["captured_runtime"]
replacements = {
    "batch48_video_output": "batch49_golden_seo_static_output",
    "batch48_video_work": "batch49_golden_seo_static_work",
    "generated_batch_48_premium_choice_video": "generated_batch_49_golden_seo_static",
    "catalog_plans_pinterest_premium_choice_videos_batch_48_200.csv": "catalog_plans_pinterest_golden_seo_static_batch_49_200.csv",
    "generated_premium_choice_video_batch_48": "generated_golden_seo_static_batch_49",
    "batch48|": "batch49|",
    "8912": "9112",
    ".mp4": ".jpg",
    "#F7F2E8": "#FBF4E8",
    "#173C36": "#4A403A",
    "#B48745": "#F4A900",
    "#D9CCB5": "#D4B896",
    "#EEE7DA": "#F3E6D4",
    "ПРЕМИАЛЬНАЯ ПОДБОРКА": "КАТАЛОГ ПРОЕКТОВ ДОМОВ",
    "ПРОЕКТ ДЛЯ ВАШЕЙ СЕМЬИ": "ГОТОВЫЙ ПРОЕКТ ДЛЯ СТРОИТЕЛЬСТВА",
    "Дом {record.area} м² — оцените проект": "Проект дома {record.area} м² с планировкой",
    "Проект №{record.project}: продуманный выбор": "Готовый проект дома №{record.project}",
    "откройте проект  •  сравните решения": "проект дома  •  характеристики  •  цена",
    "Проект №{p}: премиальный обзор": "Проект дома №{p}: характеристики",
    "Дом №{p}: полный обзор проекта": "Готовый проект дома №{p}",
    "Проект №{p}: откройте все детали": "Проект №{p}: площадь и размеры",
    "Дом №{p}: готовое решение": "Проект дома №{p} для строительства",
    "Дом №{p}: пространство для жизни": "Планировка дома №{p}",
    "Проект №{p}: архитектура в деталях": "Фасад проекта дома №{p}",
}
for old, new in replacements.items():
    if old not in runtime:
        raise RuntimeError(f"Не найден шаблон: {old}")
    runtime = runtime.replace(old, new)
runtime = runtime.replace("videos generated", "images generated")
runtime = runtime.replace("house→plans→facades videos", "static house cards")

runtime_module = types.ModuleType("batch49_runtime")
runtime_module.__file__ = str(HERE / "batch49_runtime.py")
sys.modules[runtime_module.__name__] = runtime_module
namespace = runtime_module.__dict__
exec(compile(runtime, runtime_module.__file__, "exec"), namespace)


def _font(size: int, bold: bool = False):
    path = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
    return ImageFont.truetype(path, size)


def generate_static(record):
    source = namespace["STATIC_DIR"] / f"{record.project}.jpg"
    target = namespace["VIDEO_DIR"] / f"{record.project}.jpg"
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as original:
        card = original.convert("RGB").resize((1000, 1500), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(card)
    draw.rectangle((68, 1065, 950, 1238), fill="#FBF4E8")
    draw.text((88, 1085), "ГОТОВЫЙ ПРОЕКТ ДЛЯ СТРОИТЕЛЬСТВА", font=_font(22, True), fill="#4A403A")
    seo_title = f"Проект дома {record.area} м²: характеристики"
    title_size = 39
    title_font = _font(title_size)
    while draw.textbbox((0, 0), seo_title, font=title_font)[2] > 825 and title_size > 25:
        title_size -= 1
        title_font = _font(title_size)
    draw.text((88, 1150), seo_title, font=title_font, fill="#4A403A")

    panel = (70, 1248, 930, 1480)
    draw.rounded_rectangle(panel, radius=26, fill="#4A403A")
    facts = [
        ("ПЛОЩАДЬ", f"{record.area} м²"),
        ("ЭТАЖНОСТЬ", namespace["floor_text"](record.floors)),
        ("РАЗМЕРЫ", f"{record.dimensions} м"),
    ]
    cell_width = (panel[2] - panel[0]) // 3
    for index, (label, value) in enumerate(facts):
        left = panel[0] + index * cell_width
        if index:
            draw.line((left, panel[1] + 28, left, panel[1] + 152), fill="#D4B896", width=2)
        draw.text((left + 28, panel[1] + 31), label, font=_font(21, True), fill="#D4B896")
        value_font = _font(31 if index != 2 else 27, True)
        draw.text((left + 28, panel[1] + 82), value, font=value_font, fill="#FFFFFF")
    draw.line((98, 1408, 902, 1408), fill="#D4B896", width=2)
    draw.text((98, 1430), "catalog-plans.ru", font=_font(22, True), fill="#F4A900")
    draw.text((646, 1430), "СМОТРЕТЬ ПРОЕКТ", font=_font(20, True), fill="#FFFFFF")
    card.save(target, "JPEG", quality=93, optimize=True, progressive=True)


def validate_static(records):
    files = []
    for record in records:
        path = namespace["VIDEO_DIR"] / f"{record.project}.jpg"
        if not path.exists() or path.stat().st_size < 80_000:
            raise RuntimeError(f"Некорректная карточка: {path}")
        with Image.open(path) as image:
            if image.size != (1000, 1500) or image.format != "JPEG":
                raise RuntimeError(f"Некорректный формат: {path}")
        files.append(path.name)
    return {
        "images": len(files),
        "format": "JPEG",
        "resolution": "1000x1500",
        "visualization": True,
        "seo_text": True,
        "characteristics": ["area", "floors", "dimensions"],
        "files": files,
    }


_base_write_csv = namespace["write_csv"]


def write_static_csv(records):
    _base_write_csv(records)
    csv_path = namespace["OUT_DIR"] / "catalog_plans_pinterest_golden_seo_static_batch_49_200.csv"
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    fields = list(rows[0])
    by_project = {record.project: record for record in records}
    for row in rows:
        project = row["Link"].split("/catalog/", 1)[1].split("?", 1)[0]
        record = by_project[project]
        floors = namespace["floor_text"](record.floors)
        row["Title"] = f"Проект дома №{project} площадью {record.area} м² — характеристики"
        row["Thumbnail"] = ""
        row["Description"] = (
            f"Проект дома №{project} площадью {record.area} м²: {floors}, "
            f"габариты {record.dimensions} м, материал — {record.material}. "
            "На карточке показана основная визуализация дома и ключевые характеристики. "
            "Сохраните идею для строительства и откройте каталог, чтобы посмотреть "
            "подробности проекта и актуальную стоимость."
        )
        row["Keywords"] = (
            f"проект дома {project}, проект дома {record.area} м², готовый проект дома, "
            f"характеристики дома, визуализация дома, частный дом, строительство дома, "
            f"{record.material}, catalog-plans.ru"
        )
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


namespace["generate_video"] = generate_static
namespace["validate_local"] = validate_static
namespace["write_csv"] = write_static_csv

if __name__ == "__main__":
    namespace["main"]()
