from __future__ import annotations

import os
import re
from dataclasses import replace

os.environ.setdefault("HEAD_SHA", "local")
import batch28_generate as base

ORIGINAL_PROCESS = base.old.process


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_material(heading: str) -> str:
    low = heading.lower()
    if "монолит" in low and "газобет" in low:
        return "монолитный каркас / газобетон"
    if "газобет" in low and "брус" in low:
        return "газобетон / брус"
    rules = [
        ("монолит", "монолитный каркас"),
        ("керамзитобет", "керамзитобетон"),
        ("ячеист", "ячеистый бетон"),
        ("пенобет", "пенобетон"),
        ("арболит", "арболит"),
        ("газобет", "газобетон"),
        ("керамическ", "керамический блок"),
        ("поризованн", "керамический блок"),
        ("кирпич", "кирпич"),
        ("камн", "камень"),
        ("деревянн", "дерево"),
        ("бревн", "бревно"),
        ("брус", "брус"),
        ("каркас", "каркас"),
    ]
    for token, value in rules:
        if token in low:
            return value
    return ""


def normalize_style(value: str) -> str:
    low = clean(value).lower().strip(" ,.;")
    mapping = [
        ("хай-тек", "хай-тек"),
        ("райт", "стиль Райта"),
        ("скандинав", "скандинавский"),
        ("европей", "европейский"),
        ("современн", "современный"),
        ("американ", "американский"),
        ("англий", "английский"),
        ("барнхаус", "барнхаус"),
        ("шале", "шале"),
        ("немец", "немецкий"),
        ("классическ", "классический"),
        ("средиземномор", "средиземноморский"),
        ("минимал", "минимализм"),
        ("русская усадьба", "русская усадьба"),
        ("норвеж", "норвежский"),
        ("средневек", "средневековый"),
        ("итальян", "итальянский"),
        ("модерн", "модерн"),
        ("лофт", "лофт"),
        ("чеш", "чешский"),
        ("прованс", "прованс"),
        ("русск", "русский"),
    ]
    for token, result in mapping:
        if token in low:
            return result
    return ""


def precise_metadata(record):
    heading = clean(record.h1 or record.page_title)
    low = heading.lower()

    area = ""
    match = re.search(r",\s*([\d.,]+)\s*м²", heading, re.I)
    if not match:
        match = re.search(r"([\d.,]+)\s*м²", heading, re.I)
    if match:
        area = match.group(1).replace(".", ",").strip(" ,.;")

    dimensions = ""
    match = re.search(
        r"м²,\s*([\d.,]+\s*[x×х]\s*[\d.,]+)",
        heading,
        re.I,
    )
    if match:
        dimensions = (
            match.group(1)
            .replace(".", ",")
            .replace("x", "×")
            .replace("х", "×")
            .strip(" ,.;")
        )

    floors = ""
    if "одноэтаж" in low:
        floors = "1"
    elif "двухэтаж" in low:
        floors = "2"
    elif "трехэтаж" in low or "трёхэтаж" in low:
        floors = "3"
    else:
        match = re.search(r"(?<!\d)([1-4])\s*(?:этаж|этажа|этажей)", heading, re.I)
        if match:
            floors = match.group(1)

    material_phrase = ""
    match = re.search(
        r"проект\s+.+?\s+дома\s+из\s+(.+?)(?:,|\s+[\d.,]+\s*м²)",
        heading,
        re.I,
    )
    if match:
        material_phrase = match.group(1)
    material = normalize_material(material_phrase or heading)

    style = ""
    match = re.search(r",\s*в\s+стиле\s+([^,|]+)$", heading, re.I)
    if match:
        style = normalize_style(match.group(1))
    if not style:
        match = re.search(r",\s*в\s+([^,|]+?)\s+стиле\s*$", heading, re.I)
        if match:
            style = normalize_style(match.group(1))

    # Features are deliberately omitted unless they are explicit in the H1.
    feature = ""
    explicit_features = [
        (r"\bс\s+террас", "терраса"),
        (r"\bс\s+гаражом\s+на\s+2", "гараж на 2 авто"),
        (r"\bс\s+гаражом", "гараж"),
        (r"\bс\s+панорам", "панорамные окна"),
        (r"\bс\s+плоской\s+крышей", "плоская крыша"),
        (r"\bс\s+мансард", "мансарда"),
        (r"\bсо\s+вторым\s+светом", "второй свет"),
        (r"\bс\s+саун", "сауна"),
        (r"\bс\s+бассейн", "бассейн"),
    ]
    for pattern, value in explicit_features:
        if re.search(pattern, low):
            feature = value
            break

    return replace(
        record,
        area=area,
        dimensions=dimensions,
        floors=floors,
        material=material,
        style=style,
        feature=feature,
    )


def fixed_process(project: str):
    record = ORIGINAL_PROCESS(project)
    return precise_metadata(record) if record is not None else None


base.old.process = fixed_process

if __name__ == "__main__":
    base.main()
