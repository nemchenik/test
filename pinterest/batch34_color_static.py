from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).parent
SOURCE_PATH = ROOT / "batch31_static_repair_v2.py"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

PALETTES = [
    {
        "name": "indigo_cream", "bg": "#101B35", "panel": "#F4EFE6",
        "ink": "#26334A", "muted": "#748094", "accent": "#CF875C",
        "brand": "#FAF8F4", "chip": "#FFFAF4", "border": "#DDD2C2",
        "footer": "#B66F45",
    },
    {
        "name": "teal_linen", "bg": "#0F2528", "panel": "#EFE8DE",
        "ink": "#264147", "muted": "#687A7D", "accent": "#D28D5B",
        "brand": "#FAF6F0", "chip": "#FBF7F2", "border": "#D9CDC0",
        "footer": "#B76F41",
    },
    {
        "name": "plum_rose", "bg": "#24121D", "panel": "#F5EAEC",
        "ink": "#4A2D38", "muted": "#806A73", "accent": "#D06A78",
        "brand": "#FFF7F8", "chip": "#FFF8F9", "border": "#E3CDD2",
        "footer": "#B45365",
    },
    {
        "name": "graphite_sage", "bg": "#182123", "panel": "#E9EFEB",
        "ink": "#2D3F3D", "muted": "#6C7E7A", "accent": "#9A7C57",
        "brand": "#F6FBF8", "chip": "#F8FCFA", "border": "#D0DBD6",
        "footer": "#7D6A4F",
    },
]

EYEBROWS = [
    "ГОТОВЫЙ ПРОЕКТ ДОМА",
    "ПЛАНЫ • ФАСАДЫ • РАЗМЕРЫ",
    "АРХИТЕКТУРА И ПАРАМЕТРЫ",
    "КАТАЛОГ ГОТОВЫХ ДОМОВ",
    "ПРОЕКТ ДЛЯ ВЫБОРА",
]

PANELS = [
    "Откройте проект и проверьте размеры",
    "Сравните фасады и параметры дома",
    "Посмотрите архитектуру и метраж",
    "Проверьте, подходит ли проект вам",
    "Сопоставьте фасад, площадь и размеры",
    "Оцените дом перед переходом к деталям",
    "Проверьте проект перед сохранением",
    "Откройте карточку дома на сайте",
]

FOOTERS = [
    "Планы • фасады • размеры  →",
    "Архитектура • параметры • планы  →",
    "Фасады • размеры • планировка  →",
    "Параметры • фасады • проект  →",
    "Дом • размеры • архитектура  →",
]

OPENERS = [
    "На превью использована новая цветная карточка с реальной визуализацией дома с catalog-plans.ru.",
    "В карточке показан настоящий фасад проекта в обновлённой цветовой подаче.",
    "На обложке — исходная визуализация этого дома с сайта catalog-plans.ru и новая палитра.",
    "Для пина взято реальное изображение дома и создано новое статичное оформление.",
    "Карточка использует каноническую визуализацию проекта с catalog-plans.ru.",
    "На картинке — реальный дом из карточки проекта в новом цветовом варианте.",
    "Здесь показан настоящий фасад проекта, оформленный как новая Pinterest-карточка.",
    "На превью — реальная визуализация дома с обновлённой информационной панелью.",
    "В основе карточки лежит исходное изображение проекта с catalog-plans.ru.",
    "Превью построено на базе реального изображения дома и новой цветовой схемы.",
]

MIDDLES = [
    "Такой формат помогает быстро оценить стиль дома, метраж и архитектурный образ.",
    "Это удобный способ быстро сравнить фасад, размеры и общий характер проекта.",
    "Карточка позволяет быстро понять, стоит ли открывать проект подробнее.",
    "Так проще сопоставить внешний вид дома с площадью и основными параметрами.",
    "Пин хорошо подходит для первичного отбора вариантов перед детальным просмотром.",
    "Новая палитра выделяет карточку в ленте, не перекрывая фотографию дома.",
    "Это хороший способ увидеть номер проекта, фасад и важные цифры в одном кадре.",
    "Карточка делает предпросмотр проекта более понятным и информативным.",
    "Так можно быстрее понять, соответствует ли дом ожиданиям по стилю и масштабу.",
    "Пин даёт быстрый старт для сравнения этого дома с соседними вариантами.",
]

DETAILS = [
    "Это особенно полезно, когда нужно быстро отобрать дом для постоянного проживания.",
    "Если вы сохраняете проекты в доски Pinterest, такое превью ускоряет сравнение.",
    "Такой формат хорошо работает для быстрого сохранения и возврата к проекту позже.",
    "Это помогает быстрее понять, подходит ли проект по площади и общему образу.",
    "Карточка экономит время, когда вы выбираете между несколькими похожими домами.",
    "На старте этого достаточно, чтобы решить, открывать проект или нет.",
    "Так удобнее держать в поле зрения номер проекта и ключевые параметры дома.",
    "Для первой оценки проекта такой формат особенно удобен и информативен.",
    "Это хороший вариант для понятного и чистого предпросмотра проекта.",
    "Так легче сравнивать дом по внешнему виду до глубокого изучения планировки.",
]

CLOSERS = [
    "После перехода можно изучить планы этажей, фасады, размеры и характеристики.",
    "На странице проекта доступны планировка, фасады, габариты и состав документации.",
    "В карточке проекта на сайте вы увидите планы, фасады, размеры и другие детали.",
    "После перехода откроются планы этажей, архитектурные виды и параметры проекта.",
    "На сайте можно проверить планировку, размеры, фасады и характеристики.",
    "Карточка проекта содержит планы, фасады и сведения для осознанного выбора.",
    "На странице проекта можно сравнить параметры, посмотреть планы и фасады.",
    "Дальше на сайте доступен полный набор данных по проекту дома.",
    "После перехода удобно проверить планировку, архитектуру и габариты.",
    "На catalog-plans.ru можно подробно изучить дом и его основные решения.",
]

TITLE_VARIANTS = [
    "Проект дома №{p}: новая карточка и параметры",
    "Дом №{p}: фасады, размеры и новая подача",
    "Проект №{p}: цветная карточка дома",
    "Дом №{p}: архитектура, метраж и фасады",
    "Проект дома №{p}: планировка и размеры",
    "Дом №{p}: параметры, фасады и стиль",
    "Проект №{p}: открыть карточку дома",
    "Дом №{p}: сравнить проект перед выбором",
    "Проект дома №{p}: размеры и архитектура",
    "Дом №{p}: планы, фасады и ключевые данные",
]


def font(size: int, bold: bool = False):
    return ImageFont.truetype(BOLD if bold else FONT, size=size)


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def floor_text(value: str) -> str:
    return {"1": "1 этаж", "2": "2 этажа", "3": "3 этажа", "4": "4 этажа"}.get(clean(value), "")


def rounded_image(image: Image.Image, size: tuple[int, int], radius: int) -> Image.Image:
    image = ImageOps.fit(image, size, method=Image.Resampling.LANCZOS).convert("RGBA")
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, *size), radius=radius, fill=255)
    result = Image.new("RGBA", size)
    result.paste(image, (0, 0), mask)
    return result


def wrap(draw, text: str, text_font, width: int) -> list[str]:
    lines, current = [], ""
    for word in clean(text).split():
        candidate = (current + " " + word).strip()
        if not current or draw.textbbox((0, 0), candidate, font=text_font)[2] <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def fit_font(draw, text: str, width: int, max_lines: int, start: int, minimum: int):
    for size in range(start, minimum - 1, -2):
        chosen = font(size, True)
        lines = wrap(draw, text, chosen, width)
        if len(lines) <= max_lines:
            return chosen, lines
    chosen = font(minimum, True)
    return chosen, wrap(draw, text, chosen, width)[:max_lines]


def hero(record, index: int) -> str:
    values = []
    if record.style and record.area:
        values.append(f"{record.style.capitalize()} дом {record.area} м²")
    if record.material and record.area:
        material = "дерева" if record.material == "дерево" else record.material
        values.append(f"Дом из {material} {record.area} м²")
    if record.area and record.floors:
        values.append(f"Дом {record.area} м² • {floor_text(record.floors)}")
    if record.area:
        values.append(f"Проект дома {record.area} м²")
    values.append(f"Проект дома №{record.project}")
    return values[index % len(values)]


def color_render(record, index: int, source: Path, target: Path) -> str:
    palette = PALETTES[index % len(PALETTES)]
    source_image = ImageOps.exif_transpose(Image.open(source)).convert("RGB")
    canvas = Image.new("RGB", (1000, 1500), palette["bg"])
    draw = ImageDraw.Draw(canvas)

    draw.text((48, 42), "CATALOG PLANS", fill=palette["brand"], font=font(34, True))
    pill_text = f"Проект №{record.project}"
    pill_font = font(24, True)
    pill_width = draw.textbbox((0, 0), pill_text, font=pill_font)[2] + 54
    pill_x = 952 - pill_width
    draw.rounded_rectangle((pill_x, 34, 952, 90), radius=28, outline=palette["brand"], width=2)
    draw.text((pill_x + 26, 47), pill_text, fill=palette["brand"], font=pill_font)

    image = rounded_image(source_image, (920, 610), 30)
    canvas.paste(image, (40, 120), image)
    draw.text((48, 782), EYEBROWS[index % len(EYEBROWS)], fill=palette["brand"], font=font(18, True))

    headline_font, headline_lines = fit_font(draw, hero(record, index), 900, 2, 42, 26)
    y = 820
    for line in headline_lines:
        draw.text((48, y), line, fill=palette["brand"], font=headline_font)
        y += headline_font.size + 8

    panel_top = 925
    draw.rounded_rectangle((0, panel_top, 1000, 1500), radius=46, fill=palette["panel"])
    draw.rounded_rectangle((48, panel_top + 42, 120, panel_top + 50), radius=4, fill=palette["accent"])

    panel_font, panel_lines = fit_font(draw, PANELS[index % len(PANELS)], 900, 2, 48, 28)
    y = panel_top + 82
    for line in panel_lines:
        draw.text((48, y), line, fill=palette["ink"], font=panel_font)
        y += panel_font.size + 8

    chips = []
    if record.area:
        chips.append(f"{record.area} м²")
    if record.floors:
        chips.append(floor_text(record.floors))
    if record.dimensions:
        chips.append(f"{record.dimensions} м")
    if len(chips) < 3 and record.style:
        chips.append(record.style)

    x, y = 48, panel_top + 260
    chip_font = font(24, True)
    for chip in chips[:3]:
        width = draw.textbbox((0, 0), chip, font=chip_font)[2] + 34
        draw.rounded_rectangle(
            (x, y, x + width, y + 48), radius=24,
            fill=palette["chip"], outline=palette["border"], width=1,
        )
        draw.text((x + 17, y + 11), chip, fill=palette["ink"], font=chip_font)
        x += width + 16

    footer_y = 1360
    draw.line((48, footer_y, 952, footer_y), fill=palette["border"], width=2)
    footer_font = font(22, True)
    draw.text((48, footer_y + 45), "catalog-plans.ru", fill=palette["muted"], font=footer_font)
    footer = FOOTERS[index % len(FOOTERS)]
    footer_width = draw.textbbox((0, 0), footer, font=footer_font)[2]
    draw.text((952 - footer_width, footer_y + 45), footer, fill=palette["footer"], font=footer_font)

    canvas.save(target, "JPEG", quality=90, optimize=True, progressive=True)
    return palette["name"]


def color_description(record, index: int) -> str:
    facts = []
    if record.area:
        facts.append(f"площадь {record.area} м²")
    if record.floors:
        facts.append(floor_text(record.floors))
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


def color_title(record, index: int) -> str:
    return TITLE_VARIANTS[index % len(TITLE_VARIANTS)].format(p=record.project)


source = SOURCE_PATH.read_text(encoding="utf-8")
replacements = {
    'data = b28.fetch_bytes(record.image_url)': 'data = v3.fetch_bytes(record.image_url)',
    'batch31_static_fixed_output': 'batch34_color_static_output',
    'generated_batch_31_static_fixed': 'generated_batch_34_color_static',
    'contact_sheet_batch31_static_fixed_200.jpg': 'contact_sheet_batch34_color_static_200.jpg',
    'generated_house_cards_static_fixed_batch_31': 'generated_house_cards_color_static_batch_34',
    'pin = 5512 + index': 'pin = 6112 + index',
    'catalog_plans_pinterest_house_cards_batch_31_STATIC_FIXED_200.csv': 'catalog_plans_pinterest_house_cards_batch_34_COLOR_STATIC_200.csv',
    'catalog_plans_house_cards_batch_31_static_audit.csv': 'catalog_plans_house_cards_batch_34_COLOR_STATIC_audit.csv',
    'summary_batch31_static.json': 'summary_batch34_color_static.json',
    'b28.render_without_button(': 'color_render(',
    'TITLE_PATTERNS[index % len(TITLE_PATTERNS)].format(p=record.project)': 'color_title(record, index)',
    'unique_description(record, index)': 'color_description(record, index)',
}
for old, new in replacements.items():
    if old not in source:
        raise RuntimeError(f"Expected source fragment was not found: {old}")
    source = source.replace(old, new)

namespace = {
    "__name__": "__main__",
    "__file__": str(SOURCE_PATH),
    "color_render": color_render,
    "color_description": color_description,
    "color_title": color_title,
}
exec(compile(source, str(SOURCE_PATH), "exec"), namespace)
