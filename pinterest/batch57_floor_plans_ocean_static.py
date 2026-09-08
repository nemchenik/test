#!/usr/bin/env python3
"""Generate 200 Ocean Depths cards with original floor plans and SEO copy."""

from plan_card_static_common import run_batch


if __name__ == "__main__":
    run_batch(
        batch=57,
        slug="floor_plans_ocean_static",
        style="plans_ocean",
        start_pin=10712,
        board="Планировки домов",
    )
