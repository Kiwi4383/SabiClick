#!/usr/bin/env bash
# SabiClick setup: checks dependencies, prepares config and desktop entry.
# No sudo, no network, no package writes. Run from the repo root.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/sabiclick"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"

usage() {
    cat <<EOF
Usage: ./install.sh [--check]

  --check   diagnostics only, changes nothing
  (no args) check deps, create $CONFIG_DIR and install the desktop entry
EOF
}

CHECK_ONLY=0
if [ "${1:-}" = "--check" ]; then
    CHECK_ONLY=1
elif [ $# -gt 0 ]; then
    usage >&2
    exit 2
fi

fail=0
have() { command -v "$1" >/dev/null 2>&1; }

echo "== SabiClick setup =="
if have python3; then
    echo "python3: OK ($(python3 --version 2>&1))"
else
    echo "python3: MISSING"
    fail=1
fi
SYS_TK=0; SYS_EVDEV=0
python3 -c "import tkinter" 2>/dev/null && SYS_TK=1
python3 -c "import evdev" 2>/dev/null && SYS_EVDEV=1
[ "$SYS_TK" -eq 1 ] && echo "tkinter: OK" || echo "tkinter: MISSING from system python"
[ "$SYS_EVDEV" -eq 1 ] && echo "evdev: OK" || echo "evdev: MISSING from system python"
test -w /dev/uinput 2>/dev/null \
    && echo "uinput: WRITABLE (real clicks OK)" \
    || echo "uinput: not writable (dry-run mode, see README)"

if have nix-shell; then
    echo "nix-shell: OK (launcher will use the Nix env)"
elif [ "$fail" -ne 0 ] || [ "$SYS_TK" -ne 1 ] || [ "$SYS_EVDEV" -ne 1 ]; then
    echo
    echo "Missing dependencies and no nix-shell. Easiest fix: install Nix,"
    echo "then re-run ./install.sh (or: nix develop --command python3 main.py)"
    exit 1
fi

if [ "$CHECK_ONLY" -eq 1 ]; then
    echo "check: all good"
    exit 0
fi

mkdir -p "$CONFIG_DIR"
chmod 700 "$CONFIG_DIR"
mkdir -p "$DESKTOP_DIR"
if NIX_SHELL="$(command -v nix-shell 2>/dev/null)"; then
    LAUNCHER="$NIX_SHELL $REPO/shell.nix --run \"python3 main.py\""
else
    LAUNCHER="python3 $REPO/main.py"
    echo "warning: no nix-shell found, launcher uses system python3"
fi
cat > "$DESKTOP_DIR/sabiclick.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=SabiClick
GenericName=Auto Clicker
Comment=Wayland auto-clicker
Keywords=Auto Clicker;Autoclicker;Clicker;Mouse;
Exec=$LAUNCHER
Path=$REPO
Terminal=false
Categories=Utility;
EOF
chmod +x "$REPO/run.sh" "$REPO/check.sh" "$REPO/install.sh"
echo "installed: config dir $CONFIG_DIR, desktop entry sabiclick.desktop"
