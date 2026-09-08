#!/usr/bin/env python3
"""Generate 200 Golden Hour cards with original floor plans and SEO copy."""

from plan_card_static_common import run_batch


if __name__ == "__main__":
    run_batch(
        batch=58,
        slug="floor_plans_golden_static",
        style="plans_golden",
        start_pin=10912,
        board="Проекты домов с планировкой",
    )
