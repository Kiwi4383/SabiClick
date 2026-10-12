# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
def test_jitter_bounds():
    from src.engine import ClickEngine
    calls = []

    class B:
        def click(self, b="left"):
            calls.append(1)

    class S:
        repeat_mode = "until_stopped"
        repeat_times = 1

        def should_continue(self, d):
            return d < 3

    e = ClickEngine(backend=B(), interval_ms_fn=lambda: 20,
                    state_fn=lambda: S(), button_fn=lambda: "left",
                    click_type_fn=lambda: "single", on_tick=None,
                    jitter_pct_fn=lambda: 50)
    e.start()
    e._thread.join(timeout=2.0)
    e.stop()
    assert 1 <= len(calls) <= 5


def test_stop_fast():
    import time
    from src.engine import ClickEngine

    class B:
        def click(self, b="left"):
            pass

    class S:
        repeat_mode = "until_stopped"

        def should_continue(self, d):
            return True

    e = ClickEngine(backend=B(), interval_ms_fn=lambda: 1000,
                    state_fn=lambda: S(), button_fn=lambda: "left",
                    click_type_fn=lambda: "single")
    e.start()
    time.sleep(0.05)
    t0 = time.monotonic()
    e.stop()
    e._thread.join(timeout=1.0)
    assert time.monotonic() - t0 < 1.2
