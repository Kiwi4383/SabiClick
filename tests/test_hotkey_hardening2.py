# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
def test_set_running_no_clobber_debounce():
    import time
    from src.hotkey import ToggleController
    t = ToggleController(debounce_s=10.0)
    t._last = time.monotonic() - 20.0
    t.set_running(True, notify=False, reset_debounce=False)
    assert t.running is True
    # clock untouched (20s ago): immediate physical F6 must be accepted
    assert t.handle_f6() is True
    assert t.running is False


def test_set_running_resets_when_asked():
    import time
    from src.hotkey import ToggleController
    t = ToggleController(debounce_s=10.0)
    t._last = time.monotonic() - 20.0
    before = t._last
    t.set_running(True, notify=False, reset_debounce=True)
    assert t._last >= before


def test_find_keyboards_closes_probes(monkeypatch):
    import src.hotkey as hk
    closed = []

    class FakeDev:
        def __init__(self, path):
            self.path = path

        def capabilities(self):
            return {1: [28]}

        def close(self):
            closed.append(self.path)

    monkeypatch.setattr(hk, "_HAS_EVDEV", True)
    monkeypatch.setattr(hk, "list_devices", lambda: ["/dev/input/eventX"])
    monkeypatch.setattr(hk, "InputDevice", FakeDev)
    paths = hk.find_keyboards()
    assert paths == ["/dev/input/eventX"]
    assert closed == ["/dev/input/eventX"]
