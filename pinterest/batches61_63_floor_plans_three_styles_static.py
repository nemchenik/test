#!/usr/bin/env python3
"""Generate three 200-card plan-only variants and combine them into one 600-row CSV."""

from __future__ import annotations

import csv
from pathlib import Path

from plan_card_static_common import run_batch


HERE = Path(__file__).resolve().parent
BATCHES = (
    (61, "floor_plans_sunset_static", "plans_sunset", 11512, "Планы домов и коттеджей"),
    (62, "floor_plans_forest_static", "plans_forest", 11712, "Удобные планировки домов"),
    (63, "floor_plans_minimal_static", "plans_minimal", 11912, "Современные проекты домов"),
)
COMBINED_DIR = HERE / "batches61_63_floor_plans_three_styles_static_output"
COMBINED_CSV = COMBINED_DIR / "catalog_plans_pinterest_floor_plans_three_styles_batches_61_63_600.csv"


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
    combined = [groups[variant][index] for index in range(200) for variant in range(3)]
    if len({row["Media URL"] for row in combined}) != 600:
        raise RuntimeError("В объединённом CSV обнаружены повторяющиеся Media URL")
    COMBINED_DIR.mkdir(parents=True, exist_ok=True)
    with COMBINED_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(combined)
    print(f"SUCCESS combined CSV: {COMBINED_CSV} ({len(combined)} rows)", flush=True)


if __name__ == "__main__":
    for batch, slug, style, start_pin, board in BATCHES:
        run_batch(batch=batch, slug=slug, style=style, start_pin=start_pin, board=board)
    combine_csv()
