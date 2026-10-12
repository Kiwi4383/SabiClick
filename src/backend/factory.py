# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
import logging
import os
import stat
from src.backend import DryRunBackend

log = logging.getLogger(__name__)


def _is_char_device(path: str) -> bool:
    try:
        if os.path.islink(path):
            return False
        return stat.S_ISCHR(os.stat(path).st_mode)
    except Exception:
        return False


def choose_backend(uinput_path: str = "/dev/uinput", force_dry: bool = False):
    """Never breaks: returns (backend, warning|None)."""
    if force_dry:
        return DryRunBackend(), "DRY RUN forced (force_dry)"
    if os.path.islink(uinput_path) or os.path.realpath(uinput_path) != "/dev/uinput":
        return DryRunBackend(), f"uinput path not allowed: {uinput_path}"
    if not os.path.exists(uinput_path):
        return DryRunBackend(), f"no {uinput_path}: DRY RUN"
    if not _is_char_device(uinput_path):
        return DryRunBackend(), f"{uinput_path} is not a device: DRY RUN"
    try:
        from src.backend.evdev_backend import EvdevUInputBackend
        return EvdevUInputBackend(uinput_path=uinput_path), None
    except Exception as exc:
        log.warning("real backend unavailable: %s", exc)
        return DryRunBackend(), f"DRY RUN: {exc}"
