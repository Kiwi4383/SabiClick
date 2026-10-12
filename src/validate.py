# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
"""Interval and integer validation for the GUI."""

MIN_EFFECTIVE_MS = 30


def parse_int(value, default: int = 0, lo: int = 0, hi: int = 999999) -> int:
    try:
        v = int(str(value).strip())
    except Exception:
        return default
    return max(lo, min(hi, v))


def validate_interval(h, m, s, ms) -> tuple:
    h, m, s, ms = (parse_int(h), parse_int(m), parse_int(s), parse_int(ms))
    total = h * 3600_000 + m * 60_000 + s * 1_000 + ms
    warns: list = []
    if total <= 0:
        warns.append("Interval must be greater than 0.")
    elif total < MIN_EFFECTIVE_MS:
        warns.append(f"Interval {total}ms below the ~{MIN_EFFECTIVE_MS}ms effective floor: will run at ~{MIN_EFFECTIVE_MS}ms.")
    return total, warns
