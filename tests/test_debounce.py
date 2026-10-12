# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
"""Doble F6 (evdev+Tk con foco) no debe cancelarse: antirrebote 400ms."""
import time
from src.hotkey import ToggleController


def test_rapid_double_f6_counts_as_single():
    calls = []
    c = ToggleController(on_toggle=lambda running: calls.append(running), debounce_s=0.4)
    c.handle_f6()
    time.sleep(0.05)
    c.handle_f6()  # rebote del segundo listener: debe ignorarse
    assert calls == [True]
    assert c.running is True


def test_slow_second_f6_toggles_normally():
    calls = []
    c = ToggleController(on_toggle=lambda running: calls.append(running), debounce_s=0.05)
    c.handle_f6()
    time.sleep(0.08)
    c.handle_f6()
    assert calls == [True, False]
