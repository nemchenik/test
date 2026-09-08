#!/usr/bin/env python3
"""Generate 200 warm premium cards: visualization, plans and summary."""

from plan_card_static_common import run_batch


if __name__ == "__main__":
    run_batch(batch=56, slug="visual_plans_premium_static", style="premium", start_pin=10512)
