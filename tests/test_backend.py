# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
"""Backend contract: click() records without touching the real system."""
from src.backend import DryRunBackend


def test_dry_run_records_clicks_without_side_effects():
    b = DryRunBackend()
    b.click(button="left")
    b.click(button="left")
    assert b.clicks == 2
    assert b.log == ["left", "left"]


def test_backend_move_stores_position():
    b = DryRunBackend()
    b.move(100, 200)
    assert b.position == (100, 200)
