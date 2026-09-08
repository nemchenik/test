#!/usr/bin/env python3
"""Generate 600 plain visualization-and-plan pins grouped by three SEO area queries."""

from __future__ import annotations

import csv
import os
import random
import re
from pathlib import Path

from plan_card_static_common import run_batch


HERE = Path(__file__).resolve().parent
SHARED_EXCLUDED: set[str] = set()
BATCHES = (
    (64, "raw_visual_plans_to_100", 12112, "Проекты домов до 100 м²", lambda area: area <= 100),
    (65, "raw_visual_plans_100_150", 12312, "Проекты домов 100–150 м²", lambda area: 100 < area <= 150),
    (66, "raw_visual_plans_from_150", 12512, "Проекты домов от 150 м²", lambda area: area > 150),
)
COMBINED_DIR = HERE / "batches64_66_raw_visual_plans_seo_static_output"
COMBINED_CSV = COMBINED_DIR / "catalog_plans_pinterest_raw_visual_plans_seo_batches_64_66_600.csv"


def area_value(record) -> float:
    match = re.search(r"\d+(?:[.,]\d+)?", str(record.area))
    if not match:
        raise ValueError(f"Некорректная площадь проекта {record.project}: {record.area}")
    return float(match.group(0).replace(",", "."))


def title_for(query: str):
    return lambda record, floor_text: f"{query}: проект №{record.project}, {record.area} м²"


def description_for(query: str):
    def build(record, floor_text):
        return (
            f"{query} — готовый проект №{record.project} площадью {record.area} м². "
            f"Дом: {floor_text(record.floors)}, габариты {record.dimensions} м, материал стен — {record.material}. "
            "На изображении представлены оригинальная визуализация дома и планы этажей. "
            "Сохраните проект, сравните планировку комнат и перейдите в каталог, чтобы узнать состав документации и актуальную стоимость."
        )
    return build


def keywords_for(query: str):
    def build(record, floor_text):
        return (
            f"{query.lower()}, проект дома {record.project}, дом {record.area} м², "
            f"планировка дома, планы этажей, готовый проект дома, {record.material}, catalog-plans.ru"
        )
    return build


def batch_csv(batch: int, slug: str) -> Path:
    return HERE / f"batch{batch}_{slug}_output" / f"catalog_plans_pinterest_{slug}_batch_{batch}_200.csv"


def preferred_candidates() -> list[list[str]]:
    """Reuse previously verified project IDs to avoid crawling thousands of wrong area ranges."""
    groups: list[dict[str, float]] = [{}, {}, {}]
    for path in HERE.rglob("*.csv"):
        if any(token in str(path) for token in ("batch64_", "batch65_", "batch66_", "batches64_66_")):
            continue
        try:
            with path.open(encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    project_match = re.search(r"/catalog/([^?]+)", row.get("Link", ""))
                    area_match = re.search(
                        r"(\d+(?:[.,]\d+)?)\s*м²",
                        f"{row.get('Title', '')} {row.get('Description', '')}",
                    )
                    if not project_match or not area_match:
                        continue
                    project = project_match.group(1)
                    area = float(area_match.group(1).replace(",", "."))
                    group = 0 if area <= 100 else 1 if area <= 150 else 2
                    groups[group].setdefault(project, area)
        except (OSError, csv.Error, UnicodeError):
            continue
    result = [list(group) for group in groups]
    for index, projects in enumerate(result):
        random.Random(f"raw-seo-candidates-{index}").shuffle(projects)
    if any(len(projects) < 200 for projects in result):
        raise RuntimeError(f"Недостаточно проверенных кандидатов по диапазонам: {[len(group) for group in result]}")
    print(f"preferred SEO candidates: {[len(group) for group in result]}", flush=True)
    return result


def combine_csv() -> None:
    groups = []
    fieldnames = None
    for batch, slug, *_ in BATCHES:
        with batch_csv(batch, slug).open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            if len(rows) != 200:
                raise RuntimeError(f"Партия {batch} содержит {len(rows)} строк вместо 200")
            fieldnames = fieldnames or reader.fieldnames
            groups.append(rows)
    combined = [groups[group][index] for index in range(200) for group in range(3)]
    if len({row["Media URL"] for row in combined}) != 600:
        raise RuntimeError("В объединённом CSV обнаружены повторяющиеся Media URL")
    COMBINED_DIR.mkdir(parents=True, exist_ok=True)
    with COMBINED_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(combined)
    print(f"SUCCESS combined CSV: {COMBINED_CSV} ({len(combined)} rows)", flush=True)


if __name__ == "__main__":
    candidate_groups = preferred_candidates()
    for group_index, (batch, slug, start_pin, query, area_filter) in enumerate(BATCHES):
        requested = os.environ.get("START_BATCH")
        if requested and batch < int(requested):
            continue
        existing_media = HERE / f"batch{batch}_{slug}_work" / "media"
        if existing_media.exists():
            completed = sorted(path.name for path in existing_media.iterdir() if path.is_dir())
            completed_set = set(completed)
            candidate_groups[group_index] = completed + [
                project for project in candidate_groups[group_index] if project not in completed_set
            ]
        run_batch(
            batch=batch,
            slug=slug,
            style="raw_visual_plans",
            start_pin=start_pin,
            board=query,
            exclude_published=False,
            shared_excluded=SHARED_EXCLUDED,
            record_filter=lambda record, check=area_filter: check(area_value(record)),
            title_builder=title_for(query),
            description_builder=description_for(query),
            keywords_builder=keywords_for(query),
            candidate_ids=candidate_groups[group_index],
        )
    combine_csv()
