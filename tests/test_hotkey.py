# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
"""Hotkey toggle: F6 switches start/stop even when the window is unfocused.

The real listener reads /dev/input (`input` group); here we test
the pure toggle logic, no hardware.
"""
from src.hotkey import ToggleController


def test_f6_toggles_running_state():
    import time
    calls = []
    c = ToggleController(on_toggle=lambda running: calls.append(running), debounce_s=0.05)
    assert c.running is False
    c.handle_f6()
    assert c.running is True
    time.sleep(0.08)
    c.handle_f6()
    assert c.running is False
    assert calls == [True, False]


def test_other_keys_are_ignored():
    c = ToggleController(on_toggle=lambda running: None)
    c.handle_key("a")
    assert c.running is False
