"""Orchestrator: wires the dashboard to the basic clicker and hotkeys."""

import json
import queue
import threading
import time
from pynput.mouse import Controller
from pynput import keyboard

from autoclicker.core.Clicker import Clicker
from autoclicker.core.KeyboardListener import KeyboardListener
from autoclicker.core.platform_compat import (
    AlwaysOnTopEnforcer,
    apply_window_icon,
    session_warning,
)
from autoclicker.buildinfo import build_info
from autoclicker.core.utils import resource_path, settings_path, user_config_dir
from autoclicker.ui import theme
from autoclicker.ui.dashboard import Dashboard

MAX_CPS = 1000
MIN_CPS = 1
DEFAULTS = {"cps": "20", "countdown": "5", "pause_key": "alt_gr"}


class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.mouse = Controller()
        self._always_on_top = True
        self._toast_after_id = None
        self._closed = False
        self.cps = 0
        # Worker threads (clicker, keyboard listener) never touch widgets
        # directly. They push callables here and the main loop runs them.
        self._ui_queue = queue.Queue()
        # Run state, with one owner per fact.
        # `_stop_requested` is a transient signal to the countdown thread that
        # a stop landed, cleared when the next run is claimed. A plain bool
        # could not do both jobs: written by the main loop, the countdown
        # thread and the click thread, it read as "stop pending" and "run in
        # flight" at the same time, and a Stop left it set for good.
        self._stop_requested = threading.Event()
        self._run_lock = threading.Lock()
        self._run_active = False

        self.clicker = Clicker(self.mouse, self)
        self.keyboard_listener = KeyboardListener(self)

        self._setup_window()

        self.topmost = AlwaysOnTopEnforcer(self.root)
        self.topmost.start()

        self.dashboard = Dashboard(self.root, self)
        self.dashboard.set_topmost(True)
        self.dashboard.set_state("IDLE", theme.INK_MUTED)
        self.dashboard.set_running(False)
        self.dashboard.set_build(self.build)

        self._load_settings()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        warning = session_warning()
        if warning:
            self._toast(warning)

        self._drain_ui_queue()
        self._tick_runtime()
        self._tick_cps()
        self.keyboard_listener.start()

    def _setup_window(self):
        # The build stamp in the title makes the running code verifiable.
        # If this does not match `python -m autoclicker --build`, two
        # different trees are in play.
        self.build = build_info()
        self.root.title(f"Auto Clicker - {self.build}")
        self.root.geometry(theme.WINDOW_SIZE)
        self.root.minsize(*theme.WINDOW_MIN_SIZE)
        self.root.resizable(False, False)
        self.root.configure(bg=theme.SURFACE)
        self.icon = apply_window_icon(self.root, resource_path("icon.ico"))
        try:
            self.root.wm_attributes("-topmost", True)
        except Exception:
            pass

    def _load_settings(self):
        try:
            with open(settings_path(), "r", encoding="utf-8") as fh:
                saved = json.load(fh)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return
        values = {**DEFAULTS, **saved.get("settings", {})}
        self.dashboard.set_settings(values)
        if saved.get("always_on_top") is False:
            self.dashboard.set_topmost(False)
            self.on_topmost_toggle(False)

    def _save_settings(self):
        try:
            user_config_dir()
            with open(settings_path(), "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "settings": self.dashboard.get_settings(),
                        "always_on_top": self._always_on_top,
                    },
                    fh,
                    indent=2,
                )
        except OSError:
            pass

    def _on_close(self):
        self._closed = True
        self._save_settings()
        self.clicker.stop()
        self.keyboard_listener.stop()
        self.topmost.stop()
        self.root.destroy()

    def quit(self):
        """Quit button entry point. Persists settings on the way out."""
        if self._closed:
            return
        self._on_close()

    def post_to_ui(self, fn):
        """Queue a callable to run on the Tk main loop.

        Tkinter is not thread safe. Worker threads call this instead of
        touching widgets or scheduling `after` directly.
        """
        self._ui_queue.put(fn)

    def _drain_ui_queue(self):
        while True:
            try:
                fn = self._ui_queue.get_nowait()
            except queue.Empty:
                break
            try:
                fn()
            except Exception:
                pass
        if self._closed:
            return
        try:
            self.root.after(30, self._drain_ui_queue)
        except Exception:
            # The window can be torn down between the check and the call.
            pass

    def ui_success(self):
        return theme.SUCCESS

    def ui_paused(self):
        return theme.PAUSED

    def _toast(self, message):
        # The compact layout has no event log, so surface the hint in the
        # status badge for a few seconds.
        if self._toast_after_id is not None:
            self.root.after_cancel(self._toast_after_id)
        self.dashboard.set_state("WAYLAND", theme.PAUSED)
        self._toast_after_id = self.root.after(4500, self._clear_toast)

    def _clear_toast(self):
        self._toast_after_id = None
        if not self.clicker.clicking and not self.run_active:
            self.dashboard.set_state("IDLE", theme.INK_MUTED)

    # ---- basic clicker flow ----

    def start_auto_clicker(self):
        settings = self.dashboard.settings
        # Validate every field before returning, so a bad pause key does not
        # hide a bad countdown. Each field gets its own ring and the badge
        # names the first problem.
        problems = []
        try:
            cps = int(settings.cps_entry.var.get())
            if not (MIN_CPS <= cps <= MAX_CPS):
                problems.append(("cps", "CPS 1-1000"))
        except ValueError:
            cps = None
            problems.append(("cps", "BAD CPS"))

        try:
            countdown = int(settings.countdown_entry.var.get())
            if countdown < 0:
                problems.append(("countdown", "COUNT >= 0"))
        except ValueError:
            countdown = None
            problems.append(("countdown", "BAD COUNT"))

        try:
            pause_key = keyboard.Key[settings.pause_key_entry.var.get()]
        except KeyError:
            pause_key = None
            problems.append(("pause_key", "BAD KEY"))

        settings.set_cps_invalid(any(p[0] == "cps" for p in problems))
        settings.set_countdown_invalid(any(p[0] == "countdown" for p in problems))
        settings.set_pause_key_invalid(any(p[0] == "pause_key" for p in problems))
        if problems:
            self.dashboard.set_state(problems[0][1], theme.DANGER)
            return

        self.keyboard_listener.set_pause_key(pause_key)
        if not self.begin_run():
            return
        self.cps = cps
        self.dashboard.set_cps_target(cps)
        self.dashboard.set_running(True)
        if self._toast_after_id is not None:
            self.root.after_cancel(self._toast_after_id)
            self._toast_after_id = None
        threading.Thread(
            target=self._run_countdown,
            args=(countdown, cps),
            daemon=True,
        ).start()

    def _run_countdown(self, countdown, cps):
        """Hold the run slot around the countdown thread.

        Without this a raised exception killed the daemon thread silently and
        left the slot claimed, so every later Start was refused and the app
        looked broken until it was restarted.
        """
        try:
            self.clicker.countdown(countdown, cps)
        except Exception:
            self.stop_clicking()

    def stop_clicking(self):
        self.end_run()
        self.clicker.stop()
        self.dashboard.set_cps(0)
        self.dashboard.set_running(False)
        self.dashboard.set_state("IDLE", theme.INK_MUTED)

    def toggle_pause(self):
        if self.clicker.clicking or self.run_active:
            self.stop_clicking()
        else:
            self.start_auto_clicker()

    # ---- run ownership ----

    @property
    def run_active(self):
        """True from an accepted Start until the run is stopped or ends."""
        with self._run_lock:
            return self._run_active

    @property
    def stop_requested(self):
        return self._stop_requested.is_set()

    def begin_run(self):
        """Claim the run slot and arm the countdown. False if one is live.

        Clearing the previous run's stop request belongs in here, under the
        same lock as the claim. It used to happen after the check, so a Stop
        left the flag set, every following Start was refused, and only
        restarting the app cleared it.
        """
        with self._run_lock:
            if self._run_active:
                return False
            self._stop_requested.clear()
            self._run_active = True
            return True

    def end_run(self):
        with self._run_lock:
            self._stop_requested.set()
            self._run_active = False

    # ---- always on top ----

    def toggle_always_on_top(self):
        self.on_topmost_toggle(not self._always_on_top)

    def on_topmost_toggle(self, on):
        self._always_on_top = bool(on)
        self.dashboard.set_topmost(self._always_on_top)
        try:
            self.root.wm_attributes("-topmost", self._always_on_top)
        except Exception:
            pass
        if self._always_on_top:
            self.topmost.start()
        else:
            self.topmost.stop()
        self.dashboard.set_state(
            "TOP ON" if self._always_on_top else "TOP OFF",
            theme.ACCENT if self._always_on_top else theme.INK_MUTED,
        )

    # ---- runtime ----

    def _tick_runtime(self):
        if self._closed:
            return
        if self.clicker.clicking and self.clicker.started_at is not None:
            self.dashboard.set_runtime(
                time.monotonic() - self.clicker.started_at
            )
        self.root.after(1000, self._tick_runtime)

    def _tick_cps(self):
        """Feed the dial the measured rate, not the requested one.

        Sampled here rather than posted per click: at 1000 CPS a per-click
        post is 1000 queue entries a second for a needle that cannot move
        that fast. 200 ms stays under the point where a falling rate reads
        as a lag rather than a change.
        """
        if self._closed:
            return
        self.dashboard.set_cps(self.clicker.measured_cps)
        self.root.after(200, self._tick_cps)
