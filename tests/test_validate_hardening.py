# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
def test_parse_int_caps_hi():
    from src import validate
    assert validate.parse_int("9999999", 0, hi=999999) == 999999


def test_validate_warns_effective_floor():
    from src import validate
    total, warns = validate.validate_interval(0, 0, 0, 1)
    assert total == 1
    assert any("30" in w for w in warns)
