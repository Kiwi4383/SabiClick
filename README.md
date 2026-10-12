# SabiClick 2.1

Auto-clicker for GNOME Wayland with real clicks via `/dev/uinput` and a
global hotkey (focused or not) via `/dev/input` (evdev). Original
implementation, no affiliation with OP Auto Clicker or its authors.

SPDX-License-Identifier: BSD-0-Clause — see `LICENSE` and `NOTICE`.

## Features

- Configurable interval (hours, minutes, seconds, milliseconds) with optional
  random jitter (0–50 %).
- Left / middle / right button, single or double click.
- Repeat N times or until stopped, with immediate stop.
- Cursor position: current location or noted target (`Pick location`).
- Configurable global hotkey (F6 / F7 / F8), works without focus.
- Saved profiles in `~/.config/sabiclick/config.json`.
- Automatic dry-run mode (`DryRunBackend`) without `/dev/uinput` permission:
  the app still opens and says so in the UI.

## Requirements

- Linux with GNOME Wayland, Python 3, Tkinter and `evdev`.
- For real clicks and the global hotkey: write access on `/dev/uinput` and
  read access on `/dev/input/event*` (typically the `input` group).

## Install

```bash
git clone https://github.com/Kiwi4383/SabiClick.git
cd SabiClick
./install.sh --check   # diagnostics only
./install.sh           # deps check, config dir, desktop entry
```

Run it — pick one:

```bash
nix run .                # flake app (pinned nixpkgs, see flake.lock)
nix develop --command python3 main.py   # flake dev shell
nix-shell shell.nix --run "python3 main.py"  # legacy shell
python3 main.py          # system deps already installed
```

## Permissions (real clicks + global hotkey)

Check current state (read-only, changes nothing):

```bash
./check.sh
```

```bash
groups | grep input
ls -l /dev/uinput /dev/input/event*
```

> Security note: belonging to the `input` group can read every keyboard
> (`/dev/input/event*`). Use it only while you need the global hotkey;
> without that permission the program keeps working in dry-run mode.

Example on NixOS (`configuration.nix`, replace `<your-user>`):

```nix
users.users.<your-user>.extraGroups = [ "input" ];
services.udev.extraRules = ''
  KERNEL=="uinput", GROUP="input", MODE="0660"
  KERNEL=="event*", GROUP="input", MODE="0660"
'';
```

Then: `sudo nixos-rebuild switch`, re-login and `./check.sh`.

## Usage

- Default interval: `0h 0m 0s 100ms` (~30 ms effective floor).
- `Start (F6)` / `Stop (F6)`, or the configured hotkey, focused or not
  (unfocused requires the `input` group).
- `Pick location`: 3 s to move the mouse, captures X and Y
  (`Esc` cancels; on Wayland place the cursor yourself, the relative
  backend cannot teleport it).
- `Hotkey setting`: key (F6/F7/F8), jitter and active profile.
- `Help ? >>`: About, active backend and session log.

## Project

```
main.py  run.sh  check.sh  install.sh  shell.nix  flake.nix  sabiclick.spec
src/__about__.py  src/config.py  src/validate.py
src/interval.py  src/state.py  src/engine.py
src/hotkey.py  src/app.py
src/backend/__init__.py (DryRun)
src/backend/evdev_backend.py (real Wayland)
src/backend/factory.py (picks without breaking)
tests/
LICENSE (BSD-0-Clause)  NOTICE
```

Tests:

```bash
nix-shell shell.nix --run "python3 -m pytest tests/ -v"
```

## License

BSD Zero Clause — see `LICENSE`.
