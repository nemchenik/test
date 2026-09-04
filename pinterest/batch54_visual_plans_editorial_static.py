#!/usr/bin/env python3
"""Generate 200 light editorial cards: visualization, plans and summary."""

from plan_card_static_common import run_batch


if __name__ == "__main__":
    run_batch(batch=54, slug="visual_plans_editorial_static", style="editorial", start_pin=10112)
