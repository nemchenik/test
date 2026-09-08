#!/usr/bin/env python3
"""Generate 200 Tech Innovation cards with original floor plans and SEO copy."""

from plan_card_static_common import run_batch


if __name__ == "__main__":
    run_batch(
        batch=60,
        slug="floor_plans_tech_static",
        style="plans_tech",
        start_pin=11312,
        board="Готовые проекты домов",
    )
