# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
def test_config_roundtrip(tmp_path):
    from src import config
    p = tmp_path / "c.json"
    d = config.default_config()
    config.save(str(p), d)
    assert config.load(str(p))["version"] == 1


def test_config_corrupt_recovers(tmp_path):
    from src import config
    import glob
    import os
    p = tmp_path / "c.json"
    p.write_text("{no json")
    d = config.load(str(p))
    assert d["version"] == 1
    assert glob.glob(str(p) + ".bak*")
