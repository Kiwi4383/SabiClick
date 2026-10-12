# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
def test_set_running_bypasses_debounce():
    import time
    from src.hotkey import ToggleController
    t = ToggleController()
    assert t.set_running(True) is True
    assert t.running is True
    # cambio inmediato opuesto debe aplicarse (bypass debounce)
    assert t.set_running(False) is True
    assert t.running is False


def test_handle_hotkey_alias():
    from src.hotkey import ToggleController
    t = ToggleController(debounce_s=0)
    assert hasattr(t, "handle_hotkey")
    t.handle_hotkey()
    assert t.running is True
