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
from autoclicker.core.utils import resource_path
from autoclicker.ui import theme
from autoclicker.core.utils import settings_path, user_config_dir
from autoclicker.ui.dashboard import Dashboard

MAX_CPS = 1000
MIN_CPS = 1
DEFAULTS = {"cps": "20", "countdown": "5", "pause_key": "alt_gr"}


class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.mouse = Controller()
        self._always_on_top = True
        self._pending_start = False
        self._toast_after_id = None
        self._closed = False
        # Worker threads (clicker, keyboard listener) never touch widgets
        # directly. They push callables here and the main loop runs them.
        self._ui_queue = queue.Queue()

        self.clicker = Clicker(self.mouse, self)
        self.keyboard_listener = KeyboardListener(self)

        self._setup_window()

        self.topmost = AlwaysOnTopEnforcer(self.root)
        self.topmost.start()

        self.dashboard = Dashboard(self.root, self)
        self.dashboard.set_topmost(True)
        self.dashboard.set_state("IDLE", theme.INK_MUTED)
        self.dashboard.set_running(False)

        self._load_settings()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        warning = session_warning()
        if warning:
            self._toast(warning)

        self._drain_ui_queue()
        self._tick_runtime()
        self.keyboard_listener.start()

    def _setup_window(self):
        self.root.title("Auto Clicker")
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
        if not self.clicker.clicking and not self._pending_start:
            self.dashboard.set_state("IDLE", theme.INK_MUTED)

    # ---- basic clicker flow ----

    def start_auto_clicker(self):
        try:
            cps = int(self.dashboard.settings.cps_entry.var.get())
        except ValueError:
            self.dashboard.settings.set_cps_invalid(True)
            self.dashboard.set_state("BAD CPS", theme.DANGER)
            return
        try:
            countdown = int(self.dashboard.settings.countdown_entry.var.get())
        except ValueError:
            self.dashboard.settings.set_countdown_invalid(True)
            self.dashboard.set_state("BAD COUNT", theme.DANGER)
            return
        try:
            pause_key = keyboard.Key[self.dashboard.settings.pause_key_entry.var.get()]
        except KeyError:
            self.dashboard.settings.set_pause_key_invalid(True)
            self.dashboard.set_state("BAD KEY", theme.DANGER)
            return

        cps_bad = not (MIN_CPS <= cps <= MAX_CPS)
        self.dashboard.settings.set_cps_invalid(cps_bad)
        self.dashboard.settings.set_countdown_invalid(countdown < 0)
        self.dashboard.settings.set_pause_key_invalid(False)
        if cps_bad:
            self.dashboard.set_state("CPS 1-1000", theme.DANGER)
            return
        if countdown < 0:
            self.dashboard.set_state("COUNT >= 0", theme.DANGER)
            return

        self.keyboard_listener.set_pause_key(pause_key)
        self._pending_start = True
        self.dashboard.set_cps(cps)
        self.dashboard.set_running(True)
        if self._toast_after_id is not None:
            self.root.after_cancel(self._toast_after_id)
            self._toast_after_id = None
        threading.Thread(
            target=self.clicker.countdown,
            args=(countdown, cps),
            daemon=True,
        ).start()

    def stop_clicking(self):
        self._pending_start = False
        self.clicker.stop()
        self.dashboard.set_cps(0)
        self.dashboard.set_running(False)
        self.dashboard.set_state("IDLE", theme.INK_MUTED)

    def toggle_pause(self):
        if self.clicker.clicking or self._pending_start:
            self.stop_clicking()
        else:
            self.start_auto_clicker()

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
        started = self.clicker._started_at
        if self.clicker.clicking and started is not None:
            self.dashboard.set_runtime(time.monotonic() - started)
        self.root.after(1000, self._tick_runtime)
