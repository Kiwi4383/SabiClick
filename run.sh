#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
exec nix-shell shell.nix --run "python3 main.py"
