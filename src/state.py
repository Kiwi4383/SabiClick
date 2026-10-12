# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
class ClickerState:
    def __init__(self, repeat_mode: str = "until_stopped", repeat_times: int = 1):
        self.repeat_mode = repeat_mode
        self.repeat_times = max(1, int(repeat_times))
        self._stop_requested = False

    def request_stop(self) -> None:
        self._stop_requested = True

    def reset(self) -> None:
        self._stop_requested = False

    def should_continue(self, clicks_done: int) -> bool:
        if self._stop_requested:
            return False
        if self.repeat_mode == "count":
            return clicks_done < self.repeat_times
        return True
