# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
def test_brand():
    from src.__about__ import __app_name__, __version__, APP_TITLE
    assert __app_name__ == "SabiClick"
    assert APP_TITLE == "SabiClick 2.1"


def test_no_infringing_strings():
    import pathlib
    import re
    blob = "\n".join(p.read_text() for p in [pathlib.Path("src/app.py"), pathlib.Path("README.md")])
    assert "réplica exacta" not in blob.lower()
    assert "clon wayland" not in blob.lower()
    assert "No affiliation with OP Auto Clicker" in blob
    for m in re.finditer(r"OP Auto Clicker", blob):
        start = max(0, m.start() - 20)
        assert "no affiliation" in blob[start:m.start()].lower()
