# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
"""Click engine on a separate thread. Uses an injected backend (testable)."""
import logging
import random
import threading
import time

log = logging.getLogger(__name__)


class ClickEngine:
    def __init__(self, backend, interval_ms_fn, state_fn, button_fn,
                 click_type_fn, on_tick=None, jitter_pct_fn=None,
                 double_gap_ms: int = 50, on_error=None):
        self.backend = backend
        self.interval_ms_fn = interval_ms_fn
        self.state_fn = state_fn
        self.button_fn = button_fn
        self.click_type_fn = click_type_fn
        self.on_tick = on_tick
        self.jitter_pct_fn = jitter_pct_fn or (lambda: 0)
        self.double_gap_ms = max(0, int(double_gap_ms))
        self.on_error = on_error
        self._thread = None
        self._stop_event = threading.Event()

    def start(self) -> bool:
        thr = self._thread
        if thr is not None and thr.is_alive():
            return False
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return True

    def is_alive(self) -> bool:
        thr = self._thread
        return bool(thr is not None and thr.is_alive())

    def stop(self, timeout: float = 1.0):
        self._stop_event.set()
        thr = self._thread
        if thr and thr.is_alive() and thr is not threading.current_thread():
            thr.join(timeout=timeout)

    def _sleep_interruptible(self, total_s: float):
        end = time.monotonic() + total_s
        while True:
            if self._stop_event.is_set():
                return
            remaining = end - time.monotonic()
            if remaining <= 0:
                return
            time.sleep(min(0.05, remaining))

    def _fail(self, exc: Exception):
        self._stop_event.set()
        try:
            log.exception("click backend failed: %s", exc)
        except Exception:
            pass
        if self.on_error:
            try:
                self.on_error(exc)
            except Exception:
                log.exception("on_error failed")

    def _do_single(self, btn: str):
        try:
            self.backend.click(btn)
        except Exception as exc:  # noqa: BLE001 - el hilo no debe morir en silencio
            self._fail(exc)
            raise StopIteration

    def _do_double(self, btn: str):
        dbl = getattr(self.backend, "double_click", None)
        if dbl:
            try:
                dbl(btn)
                return
            except TypeError:
                pass
            except Exception as exc:  # noqa: BLE001
                self._fail(exc)
                raise StopIteration
        try:
            self.backend.click(btn)
        except Exception as exc:  # noqa: BLE001
            self._fail(exc)
            raise StopIteration
        self._sleep_interruptible(self.double_gap_ms / 1000.0)
        if self._stop_event.is_set():
            return
        try:
            self.backend.click(btn)
        except Exception as exc:  # noqa: BLE001
            self._fail(exc)
            raise StopIteration

    def _run(self):
        done = 0
        while not self._stop_event.is_set():
            try:
                state = self.state_fn()
            except Exception as exc:  # noqa: BLE001
                self._fail(exc)
                break
            try:
                if not state.should_continue(done):
                    break
            except Exception as exc:  # noqa: BLE001
                self._fail(exc)
                break
            try:
                base = max(1, int(self.interval_ms_fn()))
            except Exception:
                base = 1
            try:
                jitter = min(50.0, max(0.0, float(self.jitter_pct_fn())))
            except Exception:
                jitter = 0.0
            delta = random.uniform(-base * jitter / 100.0, base * jitter / 100.0) if jitter else 0.0
            self._sleep_interruptible(max(1, base + delta) / 1000.0)
            if self._stop_event.is_set():
                break
            try:
                btn = self.button_fn()
                ctype = self.click_type_fn()
            except Exception as exc:  # noqa: BLE001
                self._fail(exc)
                break
            try:
                if ctype == "double":
                    self._do_double(btn)
                else:
                    self._do_single(btn)
            except StopIteration:
                break
            done += 1
            if self.on_tick:
                try:
                    self.on_tick(done)
                except Exception:
                    log.exception("on_tick failed")
