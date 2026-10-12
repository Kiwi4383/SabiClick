# SPDX-License-Identifier: BSD-0-Clause
# Copyright (c) 2026 Sabrina
"""SabiClick 2.1 GUI + Wayland backend."""
import logging
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

from src.__about__ import APP_TITLE
from src import config as cfg
from src import validate as vld

from src.interval import to_milliseconds
from src.state import ClickerState
from src.hotkey import ToggleController, find_keyboards, HOTKEYS
from src.backend.factory import choose_backend
from src.backend import DryRunBackend
from src.engine import ClickEngine

log = logging.getLogger(__name__)


class AutoClickerGUI:
    def __init__(self, root):
        self.root = root
        root.title(APP_TITLE)
        root.resizable(False, False)
        root.configure(bg="#f0f0f0")
        try:
            root.geometry("392x348")
        except Exception:
            pass

        self.backend, backend_warning = choose_backend()
        self._backend_warning = backend_warning
        self.backend_name = type(self.backend).__name__
        self.cfg_data = cfg.load()
        prof = self.cfg_data.get("profiles", {}).get(
            self.cfg_data.get("last_profile", "default"), {}) or {}
        try:
            self.jitter_pct = max(0.0, min(50.0, float(prof.get("jitter_pct", 0) or 0)))
        except Exception:
            self.jitter_pct = 0.0
        self.session_log: list = []
        self._last_ui_update = 0.0
        self._ui_queue: queue.Queue = queue.Queue()
        self._listener_stop = threading.Event()
        self._listener_devs: list = []
        self._listener_paths: list = []
        self.toggle = ToggleController(
            on_toggle=self._on_hotkey_toggle,
            hotkey_name=prof.get("hotkey", "F6"))
        if backend_warning:
            log.warning("backend: %s", backend_warning)
        self._last_engine_error: str | None = None
        self.state = ClickerState(repeat_mode="until_stopped", repeat_times=1)
        self.clicks_done = 0
        self.engine = None
        self.is_running = False
        self.pick_after_id = None

        self._build_interval(root)
        self._build_options_repeat(root)
        self._build_cursor(root)
        self._build_buttons(root)

        root.bind("<F6>", lambda e: self.toggle.handle_key("F6"))
        root.bind("<F7>", lambda e: self.toggle.handle_key("F7"))
        root.bind("<F8>", lambda e: self.toggle.handle_key("F8"))
        root.bind("<Escape>", lambda e: self._cancel_pick())
        root.protocol("WM_DELETE_WINDOW", self._on_close)
        root.after(100, self._pump_ui_queue)
        self._start_global_f6_listener()

    # ---- GUI sections (familiar layout, frozen) ----
    def _build_interval(self, root):
        tk.Label(root, text="Click interval", bg="#f0f0f0").place(x=10, y=4)
        f = tk.Frame(root, bg="#f0f0f0")
        f.place(x=10, y=24, width=372, height=30)
        self.e_hours = self._num_entry(f, 0, 0, "hours")
        self.e_mins = self._num_entry(f, 1, 0, "mins")
        self.e_secs = self._num_entry(f, 2, 0, "secs")
        self.e_ms = self._num_entry(f, 3, 100, "milliseconds", wide=True)

    def _num_entry(self, parent, col, default, suffix, wide=False):
        x = col * 95
        e = tk.Entry(parent, width=6, justify="center")
        e.insert(0, str(default))
        e.place(x=x, y=0, width=42, height=22)
        tk.Label(parent, text=suffix, bg="#f0f0f0", font=("TkDefaultFont", 8)).place(
            x=x + 44, y=2, width=52 if not wide else 62
        )
        return e

    def _build_options_repeat(self, root):
        tk.Label(root, text="Click options", bg="#f0f0f0").place(x=10, y=56)
        tk.Label(root, text="Click repeat", bg="#f0f0f0").place(x=200, y=56)

        tk.Label(root, text="Mouse button:", bg="#f0f0f0", font=("TkDefaultFont", 8)).place(x=10, y=78)
        self.cmb_button = ttk.Combobox(root, values=["Left", "Middle", "Right"], width=10, state="readonly")
        self.cmb_button.set("Left")
        self.cmb_button.place(x=90, y=76, width=90, height=22)

        tk.Label(root, text="Click type:", bg="#f0f0f0", font=("TkDefaultFont", 8)).place(x=10, y=104)
        self.cmb_type = ttk.Combobox(root, values=["Single", "Double"], width=10, state="readonly")
        self.cmb_type.set("Single")
        self.cmb_type.place(x=90, y=102, width=90, height=22)

        self.repeat_var = tk.StringVar(value="until")
        tk.Radiobutton(root, text="Repeat", variable=self.repeat_var, value="count", bg="#f0f0f0",
                       font=("TkDefaultFont", 8)).place(x=200, y=76)
        self.spin_repeat = tk.Spinbox(root, from_=1, to=999999, width=6, justify="center")
        self.spin_repeat.delete(0, "end")
        self.spin_repeat.insert(0, "1")
        self.spin_repeat.place(x=262, y=76, width=55, height=22)
        tk.Label(root, text="times", bg="#f0f0f0", font=("TkDefaultFont", 8)).place(x=320, y=78)
        tk.Radiobutton(root, text="Repeat until stopped", variable=self.repeat_var, value="until",
                       bg="#f0f0f0", font=("TkDefaultFont", 8)).place(x=200, y=102)

    def _build_cursor(self, root):
        tk.Label(root, text="Cursor position", bg="#f0f0f0").place(x=10, y=130)
        self.cursor_var = tk.StringVar(value="current")
        tk.Radiobutton(root, text="Current location", variable=self.cursor_var, value="current",
                       bg="#f0f0f0", font=("TkDefaultFont", 8)).place(x=10, y=150)
        tk.Radiobutton(root, text="", variable=self.cursor_var, value="pick",
                       bg="#f0f0f0").place(x=140, y=150)
        self.btn_pick = tk.Button(root, text="Pick location", command=self.pick_location,
                                  width=12, font=("TkDefaultFont", 8))
        self.btn_pick.place(x=160, y=148, width=95, height=24)
        tk.Label(root, text="X", bg="#f0f0f0", font=("TkDefaultFont", 8)).place(x=260, y=152)
        self.e_x = tk.Entry(root, width=6, justify="center")
        self.e_x.insert(0, "0")
        self.e_x.place(x=275, y=150, width=40, height=22)
        tk.Label(root, text="Y", bg="#f0f0f0", font=("TkDefaultFont", 8)).place(x=318, y=152)
        self.e_y = tk.Entry(root, width=6, justify="center")
        self.e_y.insert(0, "0")
        self.e_y.place(x=333, y=150, width=40, height=22)

    def _build_buttons(self, root):
        self.btn_start = tk.Button(root, text="Start (F6)", command=self.start_clicking, width=18)
        self.btn_start.place(x=10, y=190, width=175, height=36)
        self.btn_stop = tk.Button(root, text="Stop (F6)", command=self.stop_clicking,
                                  width=18, state="disabled")
        self.btn_stop.place(x=207, y=190, width=175, height=36)
        self.btn_hotkey = tk.Button(root, text="Hotkey setting", command=self.show_hotkey,
                                    width=18, font=("TkDefaultFont", 8))
        self.btn_hotkey.place(x=10, y=234, width=175, height=36)
        self.btn_help = tk.Button(root, text="Help ? >>", command=self.show_help,
                                  width=18, font=("TkDefaultFont", 8))
        self.btn_help.place(x=207, y=234, width=175, height=36)
        self.lbl_status = tk.Label(root, text="", bg="#f0f0f0", fg="#555555",
                                   font=("TkDefaultFont", 7))
        self.lbl_status.place(x=10, y=276, width=372, height=60)
        self._refresh_status("Ready. Press Start or {hk}.".format(hk=self.toggle.hotkey_name))

    # ---- logic ----
    def _get_interval_ms(self):
        return to_milliseconds(
            vld.parse_int(self.e_hours.get()),
            vld.parse_int(self.e_mins.get()),
            vld.parse_int(self.e_secs.get()),
            vld.parse_int(self.e_ms.get()))

    def _get_button(self):
        return self.cmb_button.get().lower()

    def _get_type(self):
        return "double" if self.cmb_type.get() == "Double" else "single"

    # ---- thread-safe bridge to Tk (never touch widgets off the Tk thread) ----
    def _ui_call(self, fn):
        try:
            self._ui_queue.put_nowait(fn)
        except Exception as exc:
            log.warning("UI queue full: %s", exc)

    def _pump_ui_queue(self):
        try:
            while True:
                try:
                    fn = self._ui_queue.get_nowait()
                except queue.Empty:
                    break
                try:
                    fn()
                except Exception as exc:
                    log.warning("UI callback failed: %s", exc)
        finally:
            try:
                self.root.after(100, self._pump_ui_queue)
            except Exception:
                pass  # root destroyed: end of pumping

    def toggle_f6(self):
        self.toggle.handle_f6()

    def _on_hotkey_toggle(self, running):
        # called from the evdev thread or the UI: bounce to the Tk thread via queue
        self._ui_call(lambda: self.start_clicking() if running and not self.is_running
                      else (self.stop_clicking() if not running and self.is_running else None))

    def start_clicking(self):
        if self.is_running:
            return
        self._cancel_pick()
        total, warns = vld.validate_interval(
            self.e_hours.get(), self.e_mins.get(),
            self.e_secs.get(), self.e_ms.get())
        if total <= 0:
            messagebox.showwarning(APP_TITLE, warns[0] if warns else "Interval must be greater than 0.")
            self.toggle.set_running(False, notify=False, reset_debounce=False)
            return
        if isinstance(self.backend, DryRunBackend):
            detail = self._backend_warning or "no permission on /dev/uinput, no real clicks."
            messagebox.showwarning(APP_TITLE, f"DRY RUN: {detail} See Help > Backend.")
        interval = total
        if warns:
            self._refresh_status(warns[0])
        mode = "count" if self.repeat_var.get() == "count" else "until_stopped"
        times = vld.parse_int(self.spin_repeat.get(), 1) or 1
        # immutable snapshot: the worker thread never touches Tk widgets
        snap_interval = interval
        snap_button = self._get_button()
        snap_type = self._get_type()
        snap_jitter = float(self.jitter_pct)
        state = ClickerState(repeat_mode=mode, repeat_times=times)
        self.state = state
        self.clicks_done = 0
        if self.cursor_var.get() == "pick":
            try:
                x = max(0, min(16384, vld.parse_int(self.e_x.get())))
                y = max(0, min(16384, vld.parse_int(self.e_y.get())))
                target = getattr(self.backend, "note_target", None) or self.backend.move
                target(x, y)
                if type(self.backend).__name__ == "EvdevUInputBackend":
                    self._refresh_status(
                        f"Target X={x} Y={y} noted (Wayland: place the cursor yourself; "
                        "the relative backend cannot teleport it).")
            except Exception as exc:
                log.warning("move failed: %s", exc)
        self._save_current_profile()
        old = self.engine
        if old is not None and old.is_alive():
            old.stop(timeout=1.0)
            if old.is_alive():
                self.toggle.set_running(False, notify=False, reset_debounce=False)
                self._refresh_status("Previous engine still stopping; retry in 1s.")
                return
        self.engine = ClickEngine(
            backend=self.backend,
            interval_ms_fn=lambda: snap_interval,
            state_fn=lambda s=state: s,
            button_fn=lambda: snap_button,
            click_type_fn=lambda: snap_type,
            on_tick=self._on_tick,
            jitter_pct_fn=lambda: snap_jitter,
            on_error=self._on_engine_error,
        )
        # sync toggle if Start was pressed with the mouse
        self.toggle.set_running(True, notify=False, reset_debounce=False)
        self.is_running = True
        self.engine.start()
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        hk = self.toggle.hotkey_name
        self._refresh_status(f"Clicking every {interval} ms ... ({hk} to stop)")

    def _on_engine_error(self, exc):
        self._last_engine_error = str(exc)
        self._ui_call(lambda: self._engine_failed(str(exc)))

    def _engine_failed(self, msg):
        try:
            self.stop_clicking()
        finally:
            self._refresh_status(f"Backend failed: {msg}. See Help > Backend.")

    def stop_clicking(self):
        if not self.is_running:
            self.toggle.set_running(False, notify=False, reset_debounce=False)
            return
        try:
            self.state.request_stop()
        except Exception:
            pass
        if self.engine:
            self.engine.stop(timeout=1.0)
        self.toggle.set_running(False, notify=False, reset_debounce=False)
        self.is_running = False
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self._refresh_status(f"Stopped after {self.clicks_done} clicks. Start or {self.toggle.hotkey_name} to continue.")

    def _on_tick(self, done):
        self.clicks_done = done
        try:
            self.session_log.append((time.time(), done))
            if len(self.session_log) > 500:
                del self.session_log[:-500]
        except Exception:
            log.warning("session_log failed")
        now = time.monotonic()
        if now - self._last_ui_update >= 0.2 or (
                self.state.repeat_mode == "count" and done >= self.state.repeat_times):
            self._last_ui_update = now
            hk = self.toggle.hotkey_name
            self._ui_call(lambda d=done: self._refresh_status(
                f"Clicking... {d} clicks. {hk} to stop."))
        if self.state.repeat_mode == "count" and done >= self.state.repeat_times:
            self._ui_call(self.stop_clicking)

    def pick_location(self):
        self._cancel_pick()
        self.btn_pick.config(state="disabled", text="Move in 3s... (Esc cancels)")
        self.pick_after_id = []
        self.pick_after_id.append(self.root.after(1000, lambda: self.btn_pick.config(text="Move in 2s... (Esc)")))
        self.pick_after_id.append(self.root.after(2000, lambda: self.btn_pick.config(text="Move in 1s... (Esc)")))
        self.pick_after_id.append(self.root.after(3000, self._capture_pointer))

    def _cancel_pick(self):
        try:
            for aid in (self.pick_after_id or []):
                try:
                    self.root.after_cancel(aid)
                except Exception:
                    pass
        except Exception:
            pass
        self.pick_after_id = []
        try:
            self.btn_pick.config(state="normal", text="Pick location")
        except Exception:
            pass

    def _save_current_profile(self):
        try:
            name = str(self.cfg_data.get("last_profile", "default"))[:32] or "default"
            self.cfg_data["last_profile"] = name
            self.cfg_data.setdefault("profiles", {})[name] = {
                "hours": vld.parse_int(self.e_hours.get()),
                "mins": vld.parse_int(self.e_mins.get()),
                "secs": vld.parse_int(self.e_secs.get()),
                "ms": vld.parse_int(self.e_ms.get(), 100),
                "button": self._get_button(),
                "click_type": self._get_type(),
                "repeat_mode": "count" if self.repeat_var.get() == "count" else "until_stopped",
                "repeat_times": vld.parse_int(self.spin_repeat.get(), 1) or 1,
                "x": vld.parse_int(self.e_x.get()),
                "y": vld.parse_int(self.e_y.get()),
                "jitter_pct": max(0.0, min(50.0, float(self.jitter_pct))),
                "hotkey": self.toggle.hotkey_name,
            }
            cfg.save(cfg.default_path(), self.cfg_data)
        except Exception as exc:
            log.warning("profile save failed: %s", exc)

    def _capture_pointer(self):
        self.pick_after_id = []
        try:
            x = self.root.winfo_pointerx()
            y = self.root.winfo_pointery()
            self.e_x.delete(0, "end")
            self.e_x.insert(0, str(x))
            self.e_y.delete(0, "end")
            self.e_y.insert(0, str(y))
            self.cursor_var.set("pick")
            self._refresh_status(f"Position locked: X={x} Y={y}")
        except Exception as e:
            log.warning("cursor failed: %s", e)
            self._refresh_status(f"Could not read cursor: {e}")
        try:
            self.btn_pick.config(state="normal", text="Pick location")
        except Exception:
            pass

    def _on_close(self):
        try:
            self._cancel_pick()
        except Exception:
            pass
        try:
            self._listener_stop.set()
        except Exception:
            pass
        try:
            if self.engine:
                self.engine.stop(timeout=1.0)
        except Exception:
            pass
        for d in list(self._listener_devs):
            try:
                d.close()
            except Exception:
                pass
        try:
            close = getattr(self.backend, "close", None)
            if close:
                close()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass

    # ---- global hotkey without focus (evdev) ----
    def _start_global_f6_listener(self):
        t = threading.Thread(target=self._global_listener_loop, daemon=True)
        t.start()

    def _open_keyboards(self):
        from evdev import InputDevice  # type: ignore
        for d in list(self._listener_devs):
            try:
                d.close()
            except Exception:
                pass
        self._listener_devs = []
        self._listener_paths = []
        for p in find_keyboards():
            try:
                self._listener_devs.append(InputDevice(p))
                self._listener_paths.append(p)
            except Exception as exc:
                log.warning("keyboard %s: %s", p, exc)
        return {d.fd: d for d in self._listener_devs}

    def _global_listener_loop(self):
        def status(text):
            self._ui_call(lambda: self._refresh_status(text))

        try:
            from evdev import InputDevice, ecodes  # type: ignore
        except Exception:
            hk = self.toggle.hotkey_name
            status(f"No evdev: {hk} works only with focus. Install evdev via shell.nix.")
            return
        import select
        fds = self._open_keyboards()
        if not fds:
            hk = self.toggle.hotkey_name
            status(f"{hk} global OFF: no permission on /dev/input. "
                   "Join the `input` group (see Help). Works with focus.")
        else:
            hk = self.toggle.hotkey_name
            n = len(fds)
            bn = self.backend_name
            status(f"{hk} global ON on {n} keyboard(s). Backend: {bn}")
        failures = 0
        loops = 0
        while not self._listener_stop.is_set():
            try:
                if not fds:
                    self._listener_stop.wait(5.0)
                    if self._listener_stop.is_set():
                        break
                    fds = self._open_keyboards()
                    failures = 0
                    loops = 0
                    continue
                r, _, _ = select.select(list(fds.keys()), [], [], 1.0)
                loops += 1
                if loops >= 5:
                    loops = 0
                    try:
                        if set(find_keyboards()) != set(self._listener_paths):
                            fds = self._open_keyboards()
                    except Exception as exc:
                        log.warning("hotplug rescan failed: %s", exc)
                code = self.toggle.hotkey_code
                for fd in r:
                    for ev in fds[fd].read():
                        if ev.type == 1 and ev.code == code and ev.value == 1:
                            self.toggle.handle_f6()
                failures = 0
            except Exception as exc:
                failures += 1
                log.warning("evdev listener failed %d: %s", failures, exc)
                if failures >= 3:
                    fds = self._open_keyboards()
                    failures = 0

    def show_hotkey(self):
        win = tk.Toplevel(self.root)
        win.title(f"{APP_TITLE} — Hotkey setting")
        win.resizable(False, False)
        try:
            win.geometry("380x340")
        except Exception:
            pass
        tk.Label(win, text="Start/Stop key (focused or not):").pack(pady=(10, 2))
        hk_var = tk.StringVar(value=self.toggle.hotkey_name)
        ttk.Combobox(win, textvariable=hk_var, values=["F6", "F7", "F8"],
                     width=8, state="readonly").pack()
        tk.Label(win, text="Random jitter % (0 = exact):").pack(pady=(8, 2))
        jit = tk.Spinbox(win, from_=0, to=50, width=6, justify="center")
        jit.delete(0, "end")
        jit.insert(0, str(int(self.jitter_pct)))
        jit.pack()
        tk.Label(win, text="Profile:").pack(pady=(8, 2))
        prof_var = tk.StringVar(value=self.cfg_data.get("last_profile", "default"))
        tk.Entry(win, textvariable=prof_var, justify="center", width=20).pack()
        paths = find_keyboards()
        tk.Label(win, text=f"Keyboards: {len(paths)}" +
                 ("" if paths else " (missing input group)"),
                 font=("TkDefaultFont", 8)).pack(pady=(8, 2))

        def _apply():
            hk = hk_var.get() if hk_var.get() in HOTKEYS else "F6"
            self.toggle.hotkey_name = hk
            try:
                self.jitter_pct = max(0.0, min(50.0, float(jit.get())))
            except Exception:
                self.jitter_pct = 0.0
            name = "".join(c for c in prof_var.get().strip() or "default"
                           if c.isalnum() or c in ("-", "_"))[:32] or "default"
            self.cfg_data["last_profile"] = name
            self._save_current_profile()
            self._refresh_status(f"Hotkey={hk} jitter={self.jitter_pct:g}% profile={name}")
            win.destroy()

        tk.Button(win, text="Save and close", command=_apply).pack(pady=10)
        tk.Label(win, text="NixOS: input group + udev uinput/event 0660.\nWithout permission: hotkey works only with focus.",
                 font=("TkDefaultFont", 7), fg="#555").pack()

    def show_help(self):
        from src.__about__ import __version__, __author__, __license__
        win = tk.Toplevel(self.root)
        win.title(f"{APP_TITLE} — Help")
        try:
            win.geometry("400x300")
        except Exception:
            pass
        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=6, pady=6)
        about = tk.Frame(nb)
        nb.add(about, text="About")
        tk.Label(about, justify="left", wraplength=360, text=(
            f"{APP_TITLE} (original implementation)\n"
            f"Author: {__author__} — License {__license__} v{__version__}\n"
            "No affiliation with OP Auto Clicker.\n\n"
            "Set interval, button, type, repetition and position. "
            "Start or hotkey to begin, hotkey or Stop to end "
            "(global requires the input group).\n\n./check.sh diagnoses.")).pack(padx=8, pady=8)
        be = tk.Frame(nb)
        nb.add(be, text="Backend")
        tk.Label(be, justify="left", wraplength=360, text=(
            f"Backend: {self.backend_name}\n"
            f"{'Real clicks via /dev/uinput.' if 'Evdev' in self.backend_name else 'DRY RUN: no uinput permission.'}\n"
            f"Session clicks: {self.clicks_done}")).pack(padx=8, pady=8)
        lg = tk.Frame(nb)
        nb.add(lg, text="Log")
        txt = tk.Text(lg, height=10, width=46, font=("TkDefaultFont", 7))
        txt.pack(padx=6, pady=6, fill="both", expand=True)
        try:
            import datetime as _dt
            for ts, done in self.session_log[-100:]:
                when = _dt.datetime.fromtimestamp(ts).strftime("%H:%M:%S")
                txt.insert("end", f"{when} click #{done}\n")
        except Exception as exc:
            log.warning("log failed: %s", exc)
        txt.config(state="disabled")

    def _refresh_status(self, text):
        hk = getattr(self.toggle, "hotkey_name", "F6")
        dry = " | DRY RUN" if isinstance(self.backend, DryRunBackend) else ""
        extra = f"\nBackend: {self.backend_name}{dry} | {hk}: {'ON' if self.toggle.running else 'OFF'}"
        try:
            self.lbl_status.config(text=text + extra)
        except Exception as exc:
            log.warning("status failed: %s", exc)


def main():
    root = tk.Tk()
    AutoClickerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
