# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
"""SabiClick profiles in JSON with safe recovery."""
import json
import logging
import os
import time

log = logging.getLogger(__name__)

MAX_CONFIG_BYTES = 1_000_000
HOTKEY_CHOICES = ("F6", "F7", "F8")


def sanitize_profile_name(name) -> str:
    clean = "".join(c for c in str(name or "").strip()
                    if c.isalnum() or c in ("-", "_"))[:32]
    return clean or "default"


def default_path() -> str:
    return os.path.expanduser("~/.config/sabiclick/config.json")


DEFAULT_PATH = default_path()


def _num(v, default: int = 0, lo: int = 0, hi: int = 999999) -> int:
    try:
        iv = int(str(v).strip())
    except Exception:
        return default
    if iv != iv:  # NaN guard (in case a float arrives)
        return default
    return max(lo, min(hi, iv))


def default_profile() -> dict:
    return {
        "hours": 0, "mins": 0, "secs": 0, "ms": 100,
        "button": "left", "click_type": "single",
        "repeat_mode": "until_stopped", "repeat_times": 1,
        "x": 0, "y": 0, "jitter_pct": 0, "hotkey": "F6",
    }


def default_config() -> dict:
    return {"version": 1, "last_profile": "default",
            "profiles": {"default": default_profile()}}


def sanitize_profile(raw) -> dict:
    base = default_profile()
    if not isinstance(raw, dict):
        return base
    out = dict(base)
    for k in ("hours", "mins", "secs", "ms", "repeat_times", "x", "y"):
        if k in raw:
            out[k] = _num(raw[k], base[k])
    btn = str(raw.get("button", "left")).lower()
    out["button"] = btn if btn in ("left", "middle", "right", "center") else "left"
    ct = str(raw.get("click_type", "single")).lower()
    out["click_type"] = "double" if ct == "double" else "single"
    rm = str(raw.get("repeat_mode", "until_stopped"))
    out["repeat_mode"] = "count" if rm == "count" else "until_stopped"
    try:
        jit = float(raw.get("jitter_pct", 0))
    except Exception:
        jit = 0.0
    if jit != jit or jit == float("inf") or jit == float("-inf"):
        jit = 0.0
    out["jitter_pct"] = max(0.0, min(50.0, jit))
    hk = str(raw.get("hotkey", "F6")).upper()
    out["hotkey"] = hk if hk in HOTKEY_CHOICES else "F6"
    return out


def list_profiles(data: dict) -> list:
    profs = data.get("profiles", {}) if isinstance(data, dict) else {}
    return sorted(k for k in profs if isinstance(k, str)) or ["default"]


def load(path: str | None = None) -> dict:
    path = path or default_path()
    try:
        if os.path.exists(path) and os.path.getsize(path) > MAX_CONFIG_BYTES:
            raise ValueError("config file too large")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "profiles" not in data:
            raise ValueError("invalid schema")
        clean = default_config()
        profiles = data.get("profiles", {})
        if not isinstance(profiles, dict):
            raise ValueError("invalid profiles")
        for name, raw in profiles.items():
            if not isinstance(name, str):
                continue
            stripped = name.strip()
            if not stripped:
                continue
            clean_name = sanitize_profile_name(stripped)
            if clean_name == "default" and stripped != "default":
                continue  # junk colliding with default is discarded
            clean["profiles"][clean_name] = sanitize_profile(raw)
        last = sanitize_profile_name(data.get("last_profile", "default"))
        clean["last_profile"] = last if last in clean["profiles"] else "default"
        clean["version"] = 1
        return clean
    except FileNotFoundError:
        return default_config()
    except Exception as exc:  # noqa: BLE001 - documented safe recovery
        log.warning("corrupt config %s: %s", path, exc)
        try:
            if os.path.exists(path) and not os.path.islink(path):
                stamp = f"{time.strftime('%Y%m%d-%H%M%S')}-{os.getpid()}"
                bak = f"{path}.bak-{stamp}"
                src_fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
                try:
                    dst_fd = os.open(bak, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                except FileExistsError:
                    bak = f"{bak}-{os.getpid()}"
                    dst_fd = os.open(bak, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                try:
                    with os.fdopen(src_fd, "rb") as src, os.fdopen(dst_fd, "wb") as dst:
                        dst.write(src.read())
                except BaseException:
                    try:
                        os.unlink(bak)
                    except Exception:
                        pass
                    raise
        except Exception:
            pass
        return default_config()


def save(path: str, data: dict) -> None:
    parent = os.path.dirname(path) or "."
    if os.path.islink(parent) or os.path.islink(path):
        raise ValueError("symlink path rejected")
    try:
        parent_stat = os.stat(parent) if os.path.exists(parent) else None
        if parent_stat is not None and not os.path.isdir(parent):
            raise ValueError("parent is not a directory")
    except ValueError:
        raise
    except Exception:
        pass
    os.makedirs(parent, exist_ok=True)
    try:
        os.chmod(parent, 0o700)
    except Exception:
        pass
    tmp = path + ".tmp"
    try:
        os.unlink(tmp)
    except FileNotFoundError:
        pass
    except Exception:
        pass
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    fd = os.open(tmp, flags, 0o600)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except BaseException:
        try:
            os.unlink(tmp)
        except Exception:
            pass
        raise
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass
