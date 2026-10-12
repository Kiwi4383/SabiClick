# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
def test_stop_joins_thread():
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
    e.start()
    time.sleep(0.05)
    e.stop(timeout=1.0)
    assert not (e._thread and e._thread.is_alive())


def test_backend_error_calls_on_error_and_stops():
    import time
    from src.engine import ClickEngine

    class Bad:
        def click(self, b="left"):
            raise OSError("uinput desconectado")

    class S:
        repeat_mode = "until_stopped"

        def should_continue(self, d):
            return True

    errors = []
    e = ClickEngine(backend=Bad(), interval_ms_fn=lambda: 10,
                    state_fn=lambda: S(), button_fn=lambda: "left",
                    click_type_fn=lambda: "single",
                    on_error=lambda exc: errors.append(str(exc)))
    e.start()
    e._thread.join(timeout=2.0)
    assert errors and "uinput" in errors[0]


def test_jitter_clamped_to_50():
    from src.engine import ClickEngine
    calls = []

    class B:
        def click(self, b="left"):
            calls.append(1)

    class S:
        repeat_mode = "until_stopped"

        def should_continue(self, d):
            return d < 2

    e = ClickEngine(backend=B(), interval_ms_fn=lambda: 20,
                    state_fn=lambda: S(), button_fn=lambda: "left",
                    click_type_fn=lambda: "single",
                    jitter_pct_fn=lambda: 200)
    e.start()
    e._thread.join(timeout=2.0)
    # con clamp 50%, no debe colgarse ni hacer busy-loop
    assert 1 <= len(calls) <= 3
