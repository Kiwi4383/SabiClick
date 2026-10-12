# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
def test_profile_name_sanitized_on_load(tmp_path):
    import json
    from src import config
    d = config.default_config()
    d["profiles"]["../x\nFAKE\n"] = config.default_profile()
    d["profiles"]["ok-name_1"] = config.default_profile()
    p = tmp_path / "c.json"
    p.write_text(json.dumps(d))
    out = config.load(str(p))
    assert "../x\nFAKE\n" not in out["profiles"]
    assert "ok-name_1" in out["profiles"]


def test_save_enforces_0600(tmp_path):
    import os
    from src import config
    p = str(tmp_path / "c.json")
    open(p + ".tmp", "w").close()
    os.chmod(p + ".tmp", 0o644)
    config.save(p, config.default_config())
    assert (os.stat(p).st_mode & 0o777) == 0o600
    assert not os.path.exists(p + ".tmp")


def test_save_refuses_symlink_parent(tmp_path):
    import os
    from src import config
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    os.symlink(str(real), str(link))
    try:
        config.save(str(link / "c.json"), config.default_config())
    except ValueError:
        return
    raise AssertionError("should have rejected symlink parent")


def test_is_char_device(tmp_path):
    import os
    from src.backend.factory import _is_char_device
    assert _is_char_device("/dev/null") is True
    f = tmp_path / "regular"
    f.write_bytes(b"x")
    assert _is_char_device(str(f)) is False
    assert _is_char_device("/no/existe") is False
