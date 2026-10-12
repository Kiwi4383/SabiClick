# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
def test_start_returns_status_and_is_alive():
    import time
    from src.engine import ClickEngine

    class B:
        def click(self, b="left"):
            pass

    class S:
        repeat_mode = "until_stopped"

        def should_continue(self, d):
            return True

    e = ClickEngine(backend=B(), interval_ms_fn=lambda: 50,
                    state_fn=lambda: S(), button_fn=lambda: "left",
                    click_type_fn=lambda: "single")
    assert e.start() is True
    assert e.is_alive() is True
    assert e.start() is False  # segundo start no duplica: avisa False
    e.stop(timeout=1.0)
    assert e.is_alive() is False


def test_failing_on_error_does_not_kill_silently():
    import logging
    from src.engine import ClickEngine

    class Bad:
        def click(self, b="left"):
            raise OSError("uinput caido")

    class S:
        repeat_mode = "until_stopped"

        def should_continue(self, d):
            return True

    def bad_hook(exc):
        raise RuntimeError("hook roto")

    e = ClickEngine(backend=Bad(), interval_ms_fn=lambda: 10,
                    state_fn=lambda: S(), button_fn=lambda: "left",
                    click_type_fn=lambda: "single", on_error=bad_hook)
    e.start()
    e._thread.join(timeout=2.0)
    assert not e.is_alive()
