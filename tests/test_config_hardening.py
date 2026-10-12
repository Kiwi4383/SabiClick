# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
def test_load_sanitizes_bad_types():
    from src import config
    import json
    import tempfile, os
    d = config.default_config()
    d["profiles"]["default"]["jitter_pct"] = "xxx"
    d["profiles"]["default"]["hotkey"] = "F99"
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(d, f)
        p = f.name
    try:
        out = config.load(p)
        prof = out["profiles"]["default"]
        assert prof["jitter_pct"] == 0
        assert prof["hotkey"] == "F6"
    finally:
        os.unlink(p)
        import glob
        for b in glob.glob(p + ".bak*"):
            os.unlink(b)


def test_list_profiles():
    from src import config
    d = config.default_config()
    assert "default" in config.list_profiles(d)


def test_save_atomic_private(tmp_path):
    import os
    from src import config
    p = str(tmp_path / "c.json")
    config.save(p, config.default_config())
    assert os.path.exists(p)
