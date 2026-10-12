# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
"""The Wayland backend must advertise itself as a mouse (REL_X/REL_Y),
otherwise libinput/GNOME ignores clicks without any error."""
from src.backend.evdev_backend import required_events


def test_backend_advertises_pointer_axes():
    ev = required_events()
    # EV_REL == 2 must exist with REL_X (0) and REL_Y (1)
    assert 2 in ev, "missing EV_REL: GNOME will ignore clicks"
    assert 0 in ev[2] and 1 in ev[2]
