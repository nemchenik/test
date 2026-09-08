#!/usr/bin/env python3
"""Generate 400 plain visualization-and-plan pins for one- and two-storey SEO boards."""

from __future__ import annotations

import csv
import os
import random
import re
from pathlib import Path

from plan_card_static_common import run_batch


HERE = Path(__file__).resolve().parent
RECENT_CSV = HERE / "batches64_66_raw_visual_plans_seo_static_output" / "catalog_plans_pinterest_raw_visual_plans_seo_batches_64_66_600.csv"
BATCHES = (
    (67, "raw_visual_plans_one_storey", 12712, "Одноэтажные дома с планировкой", "1"),
    (68, "raw_visual_plans_two_storey", 12912, "Двухэтажные дома с планировкой", "2"),
)
COMBINED_DIR = HERE / "batches67_68_raw_visual_plans_floors_seo_static_output"
COMBINED_CSV = COMBINED_DIR / "catalog_plans_pinterest_raw_visual_plans_floors_seo_batches_67_68_400.csv"


def project_from_link(link: str) -> str | None:
    match = re.search(r"/catalog/([^?]+)", link)
    return match.group(1) if match else None


def recent_project_ids() -> set[str]:
    if not RECENT_CSV.exists():
        return set()
    with RECENT_CSV.open(encoding="utf-8-sig", newline="") as handle:
        return {project for row in csv.DictReader(handle) if (project := project_from_link(row.get("Link", "")))}


def preferred_candidates(excluded: set[str]) -> list[list[str]]:
    groups: list[dict[str, None]] = [{}, {}]
    target_fragment = "batches67_68_raw_visual_plans_floors_seo"
    for path in HERE.rglob("*.csv"):
        if target_fragment in str(path):
            continue
        try:
            with path.open(encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    project = project_from_link(row.get("Link", ""))
                    if not project or project in excluded:
                        continue
                    text = f"{row.get('Title', '')} {row.get('Description', '')}".lower()
                    floor_match = re.search(r"(?:дом:\s*)?([12])\s+этаж", text)
                    if floor_match:
                        groups[int(floor_match.group(1)) - 1].setdefault(project, None)
        except (OSError, csv.Error, UnicodeError):
            continue
    result = [list(group) for group in groups]
    for index, projects in enumerate(result):
        random.Random(f"raw-floor-seo-{index}").shuffle(projects)
    if any(len(projects) < 200 for projects in result):
        raise RuntimeError(f"Недостаточно кандидатов по этажности: {[len(group) for group in result]}")
    print(f"preferred floor candidates: {[len(group) for group in result]}", flush=True)
    return result


def floor_matches(record, expected: str) -> bool:
    return str(record.floors).strip() == expected


def title_for(query: str):
    return lambda record, floor_text: f"{query}: проект №{record.project}, {record.area} м²"


def description_for(query: str):
    def build(record, floor_text):
        return (
            f"{query} — готовый проект №{record.project} площадью {record.area} м². "
            f"Характеристики: {floor_text(record.floors)}, габариты {record.dimensions} м, "
            f"материал стен — {record.material}. На изображении показаны оригинальная визуализация дома "
            "и реальные планы этажей. Сохраните планировку для сравнения и откройте проект в каталоге, "
            "чтобы посмотреть состав документации и актуальную стоимость."
        )
    return build


def keywords_for(query: str):
    def build(record, floor_text):
        return (
            f"{query.lower()}, проект дома {record.project}, дом {record.area} м², "
            f"{floor_text(record.floors)}, планировка дома, планы этажей, готовый проект дома, "
            f"{record.material}, catalog-plans.ru"
        )
    return build


def batch_csv(batch: int, slug: str) -> Path:
    return HERE / f"batch{batch}_{slug}_output" / f"catalog_plans_pinterest_{slug}_batch_{batch}_200.csv"


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
    combined = [groups[group][index] for index in range(200) for group in range(2)]
    if len({row["Media URL"] for row in combined}) != 400:
        raise RuntimeError("В объединённом CSV обнаружены повторяющиеся Media URL")
    COMBINED_DIR.mkdir(parents=True, exist_ok=True)
    with COMBINED_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(combined)
    print(f"SUCCESS combined CSV: {COMBINED_CSV} ({len(combined)} rows)", flush=True)


if __name__ == "__main__":
    excluded = recent_project_ids()
    candidate_groups = preferred_candidates(excluded)
    shared_excluded = set(excluded)
    for index, (batch, slug, start_pin, query, expected_floor) in enumerate(BATCHES):
        requested = os.environ.get("START_BATCH")
        if requested and batch < int(requested):
            continue
        run_batch(
            batch=batch,
            slug=slug,
            style="raw_visual_plans",
            start_pin=start_pin,
            board=query,
            exclude_published=False,
            shared_excluded=shared_excluded,
            record_filter=lambda record, expected=expected_floor: floor_matches(record, expected),
            title_builder=title_for(query),
            description_builder=description_for(query),
            keywords_builder=keywords_for(query),
            candidate_ids=candidate_groups[index],
        )
    combine_csv()
