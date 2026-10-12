# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
class DryRunBackend:
    """Test backend: touches nothing on the system, only records."""

    def __init__(self):
        self.clicks = 0
        self.log: list = []
        self.position = (0, 0)

    def click(self, button: str = "left") -> None:
        self.clicks += 1
        self.log.append(button)

    def note_target(self, x: int, y: int) -> None:
        self.position = (max(0, min(16384, int(x))), max(0, min(16384, int(y))))

    def move(self, x: int, y: int) -> None:
        self.note_target(x, y)

    def close(self) -> None:
        pass
