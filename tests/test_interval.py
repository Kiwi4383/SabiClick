# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
"""Interval: hours/mins/secs/millis -> total milliseconds."""
from src.interval import to_milliseconds


def test_combines_all_units():
    assert to_milliseconds(hours=1, minutes=2, seconds=3, milliseconds=400) == (
        1 * 3600_000 + 2 * 60_000 + 3 * 1_000 + 400
    )


def test_defaults_to_100ms_like_photo():
    assert to_milliseconds(hours=0, minutes=0, seconds=0, milliseconds=100) == 100


def test_zero_interval_is_invalid():
    assert to_milliseconds(hours=0, minutes=0, seconds=0, milliseconds=0) == 0
