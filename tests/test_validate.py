# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
def test_validate_zero():
    from src import validate
    total, warns = validate.validate_interval(0, 0, 0, 0)
    assert total == 0 and len(warns) == 1


def test_validate_negative_clamped():
    from src import validate
    assert validate.parse_int("-5", 0) == 0
