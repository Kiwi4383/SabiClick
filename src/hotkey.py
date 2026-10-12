# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
"""Hotkey toggle + global listener via evdev (Wayland, unfocused).

Why evdev: on GNOME Wayland there are no global hotkeys for regular
apps. Reading /dev/input/event* we see the key even when the window
is unfocused. Requires membership in the `input` group.
"""
import threading
import time

try:
    from evdev import InputDevice, ecodes, list_devices  # type: ignore
    _HAS_EVDEV = True
except Exception:
    _HAS_EVDEV = False

HOTKEYS = {"F6": 64, "F7": 65, "F8": 66}
F6_CODE = HOTKEYS["F6"]  # compat: KEY_F6 on Linux input
KEY_ENTER = 28
EV_KEY = 1


class ToggleController:
    def __init__(self, on_toggle=None, debounce_s: float = 0.4,
                 hotkey_name: str = "F6"):
        self.running = False
        self._on_toggle = on_toggle
        self._debounce = float(debounce_s)
        self._last = 0.0
        self._lock = threading.Lock()
        self.hotkey_name = hotkey_name if hotkey_name in HOTKEYS else "F6"

    @property
    def hotkey_code(self) -> int:
        return HOTKEYS.get(self.hotkey_name, 64)

    def set_running(self, value: bool, notify: bool = True,
                  reset_debounce: bool = True) -> bool:
        import time as _time
        with self._lock:
            self.running = bool(value)
            if reset_debounce:
                self._last = _time.monotonic()
            state = self.running
        if notify and self._on_toggle:
            self._on_toggle(state)
        return True

    def handle_f6(self):
        now = time.monotonic()
        with self._lock:
            if now - self._last < self._debounce:
                return False
            self._last = now
            self.running = not self.running
            state = self.running
        if self._on_toggle:
            self._on_toggle(state)
        return True

    def handle_hotkey(self):
        return self.handle_f6()

    def handle_key(self, key_name: str):
        if key_name == self.hotkey_name:
            self.handle_f6()


def find_keyboards():
    """Return /dev/input/event* paths that are keyboards. Empty if no permission."""
    if not _HAS_EVDEV:
        return []
    paths = []
    try:
        for path in list_devices():
            dev = None
            try:
                dev = InputDevice(path)
                caps = dev.capabilities()
                keys = caps.get(EV_KEY, [])  # EV_KEY
                if KEY_ENTER in keys or F6_CODE in keys:
                    paths.append(path)
            except Exception:
                continue
            finally:
                try:
                    if dev is not None:
                        dev.close()
                except Exception:
                    pass
    except Exception:
        return []
    return paths
