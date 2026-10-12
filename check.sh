#!/usr/bin/env bash
# Read-only diagnostics, changes nothing.
echo "== SabiClick check (read-only) =="
test -f LICENSE && echo "LICENSE: OK" || echo "LICENSE: missing"
echo "USER=$USER groups=$(groups)"
echo
echo "-- /dev/uinput --"
ls -l /dev/uinput 2>&1 || echo "no /dev/uinput"
test -w /dev/uinput && echo "uinput: WRITABLE (real clicks OK)" || echo "uinput: NOT writable -> dry-run mode (missing input group / udev rule)"
echo
echo "-- /dev/input/event* (keyboards for global hotkey) --"
ls -l /dev/input/event* 2>&1 | head -n10
echo
echo "-- python env --"
nix-shell shell.nix --run "python3 -c 'import sys; print(sys.version)'; python3 -c 'import tkinter; print(\"tk\", tkinter.TkVersion)'" 2>&1 | tail -n5
nix-shell shell.nix --run "python3 -m pytest tests/ -q" 2>&1 | tail -n5
echo
echo "For focus-free hotkey + real clicks you need:"
echo "  input group + udev uinput/event* 0660 (see README)"
