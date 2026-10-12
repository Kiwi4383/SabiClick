# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
"""ClickerState: repeat N times vs repeat-until-stopped."""
from src.state import ClickerState


def test_repeat_n_times_stops_at_count():
    s = ClickerState(repeat_mode="count", repeat_times=3)
    assert s.should_continue(clicks_done=0) is True
    assert s.should_continue(clicks_done=2) is True
    assert s.should_continue(clicks_done=3) is False


def test_repeat_until_stopped_never_auto_stops():
    s = ClickerState(repeat_mode="until_stopped", repeat_times=1)
    assert s.should_continue(clicks_done=0) is True
    assert s.should_continue(clicks_done=9999) is True


def test_stop_request_halts_even_until_stopped():
    s = ClickerState(repeat_mode="until_stopped", repeat_times=1)
    s.request_stop()
    assert s.should_continue(clicks_done=0) is False
