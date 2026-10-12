# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
def to_milliseconds(hours: int, minutes: int, seconds: int, milliseconds: int) -> int:
    return int(hours) * 3600_000 + int(minutes) * 60_000 + int(seconds) * 1_000 + int(milliseconds)
