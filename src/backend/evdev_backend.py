# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
"""Native Wayland backend via /dev/uinput (evdev).

Creates a virtual mouse: works on GNOME Wayland without X.
Requires write permission on /dev/uinput (`input` group on NixOS
with the right udev rule). Without permission it raises PermissionError
and the factory falls back to DryRun without breaking.
"""
import logging
import os
import time

log = logging.getLogger(__name__)

try:
    from evdev import UInput, ecodes  # type: ignore
    _HAS_EVDEV = True
except Exception:
    _HAS_EVDEV = False


def required_events():
    from evdev import ecodes  # type: ignore
    return {
        ecodes.EV_KEY: [ecodes.BTN_LEFT, ecodes.BTN_MIDDLE, ecodes.BTN_RIGHT],
        ecodes.EV_REL: [ecodes.REL_X, ecodes.REL_Y],
    }


class EvdevUInputBackend:
    def __init__(self, uinput_path: str = "/dev/uinput"):
        real = os.path.realpath(uinput_path)
        if real != "/dev/uinput":
            raise ValueError(f"uinput_path not allowed: {uinput_path}")
        if not _HAS_EVDEV:
            raise RuntimeError("evdev not available")
        try:
            self._ui = UInput(
                events=required_events(),
                name="sabiclick",
                devnode=real,
            )
        except PermissionError:
            raise PermissionError(f"no write access on {real} (missing input group?)")
        self.clicks = 0
        self._last_move = (0, 0)

    def _code(self, button: str) -> int:
        from evdev import ecodes  # type: ignore
        return {
            "left": ecodes.BTN_LEFT,
            "middle": ecodes.BTN_MIDDLE,
            "center": ecodes.BTN_MIDDLE,
            "right": ecodes.BTN_RIGHT,
        }.get(button, ecodes.BTN_LEFT)

    def click(self, button: str = "left") -> None:
        code = self._code(button)
        self._ui.write(1, code, 1)
        self._ui.syn()
        time.sleep(0.02)
        self._ui.write(1, code, 0)
        self._ui.syn()
        time.sleep(0.01)
        self.clicks += 1

    def double_click(self, button: str = "left") -> None:
        self.click(button)
        time.sleep(0.05)
        self.click(button)

    def note_target(self, x: int, y: int) -> None:
        """Record target. Relative Wayland/uinput cannot teleport: the click
        lands wherever the cursor is. The GUI must say so, not fake success."""
        self._last_move = (max(0, min(16384, int(x))), max(0, min(16384, int(y))))

    def move(self, x: int, y: int) -> None:
        self.note_target(x, y)

    def close(self) -> None:
        try:
            self._ui.close()
        except Exception:
            pass
