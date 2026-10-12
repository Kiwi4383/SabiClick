# AGENTS.md

SabiClick 2.1: auto-clicker for GNOME Wayland (Python + Tkinter + evdev/uinput).
Original implementation, BSD-0-Clause license. Main GUI layout frozen for
muscle memory: do not move widgets or the `392x348` geometry.

## Layout

- `main.py` — entry point
- `src/app.py` — Tk GUI + wiring (do not touch `place()`)
- `src/engine.py` — click engine on a thread (`stop(timeout)`, `on_error`)
- `src/hotkey.py` — `ToggleController` + `find_keyboards` (evdev)
- `src/config.py` — profiles at `~/.config/sabiclick/config.json` (schema + 0600)
- `src/validate.py`, `src/interval.py`, `src/state.py`, `src/__about__.py`
- `src/backend/` — `DryRunBackend`, `EvdevUInputBackend`, `factory`
- `tests/` — pytest, one file per area
- `run.sh`, `check.sh` (read-only), `install.sh`, `shell.nix`, `flake.nix`, `sabiclick.spec`

## Verify

```sh
nix-shell shell.nix --run "python3 -m pytest tests/ -q"
```

Suite must be green before committing.

## What goes into the repo (code only)

Yes: code, tests, `README.md`, `LICENSE`, `NOTICE`, `AGENTS.md`,
`shell.nix`, `flake.nix`, `sabiclick.spec`, `run.sh`, `check.sh`, `install.sh`.

No: `docs/superpowers/`, `.superpowers/`, `build/`, `dist/`,
`__pycache__/`, `.pytest_cache/`, `*.bak*` (already in `.gitignore`).
Nothing internal to the plugin (specs, plans, ledgers, briefs) leaves the
local machine: do not paste it into `AGENTS.md` or the opencode system
prompt either. Keep `AGENTS.md` to minimal product context.

## Commits

1. Message via the `nombres-commits` skill: Conventional Commits
   `type(scope): subject`, type derived from the staged diff, imperative,
   lowercase, no trailing period, max 72 chars, in English.
2. Identity per repo host (repo-local, never global):

   | Host | `user.name` | `user.email` |
   |------|-------------|--------------|
   | GitHub (`Kiwi4383/*`) | `Kiwi4383` | `334576843+Kiwi4383@users.noreply.github.com` |
   | GitLab (`Brina-git/*`) | `Brina-git` | `brinagit.reopen395@simplelogin.com` |

   ```sh
   git config user.name "Kiwi4383"
   git config user.email "334576843+Kiwi4383@users.noreply.github.com"
   git config commit.gpgsign true
   git config user.signingkey 3351F2CFF552BA7A
   ```
3. Always signed: `git commit -S -m "..."`. Verify with
   `git log --show-signature -1` (expected: `Good signature`).
4. Push over SSH (`git@github.com:...` / `git@gitlab.com:...`).
