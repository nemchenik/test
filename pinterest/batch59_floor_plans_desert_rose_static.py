#!/usr/bin/env python3
"""Generate 200 Desert Rose cards with original floor plans and SEO copy."""

from plan_card_static_common import run_batch


if __name__ == "__main__":
    run_batch(
        batch=59,
        slug="floor_plans_desert_rose_static",
        style="plans_desert_rose",
        start_pin=11112,
        board="Планировки частных домов",
    )
