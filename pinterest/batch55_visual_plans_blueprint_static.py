#!/usr/bin/env python3
"""Generate 200 blueprint cards: visualization, plans and summary."""

from plan_card_static_common import run_batch


if __name__ == "__main__":
    run_batch(batch=55, slug="visual_plans_blueprint_static", style="blueprint", start_pin=10312)
