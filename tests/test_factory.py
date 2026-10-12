# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
"""Factory elige backend sin romper: uinput si hay permiso, si no DryRun."""
from src.backend.factory import choose_backend
from src.backend import DryRunBackend


def test_chooses_dryrun_when_no_uinput_permission(tmp_path):
    fake_uinput = tmp_path / "uinput"
    fake_uinput.write_bytes(b"")
    import os
    os.chmod(fake_uinput, 0o000)
    b, warn = choose_backend(uinput_path=str(fake_uinput), force_dry=True)
    assert isinstance(b, DryRunBackend)
    assert warn
