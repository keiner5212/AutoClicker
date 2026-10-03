"""Compact two-column dashboard: dial + status left, inputs right.

Single surface color, subtle dual shadows, thin tracked typography.
Left column: gauge and status. Right column: settings and actions.
"""

import tkinter as tk

from autoclicker.ui import theme
from autoclicker.ui.widgets import (
    NeumoCard,
    NeumoCardTitle,
    NeumoGauge,
    NeumoPillButton,
    NeumoPowerDot,
    NeumoSoftEntry,
    NeumoStatusBadge,
    NeumoToggle,
    NeumoTooltip,
    _resolve,
)

COLUMN_GAP = theme.SPACE_4
CARD_GAP = theme.SPACE_3
OUTER_PAD = theme.SPACE_4


class DialCard:
    """Left column: gauge with live CPS readout."""

    def __init__(self, parent, app):
        self.app = app
        self.card = NeumoCard(parent, padding=theme.CARD_PADDING_TIGHT)
        self._build()

    def _build(self):
        inner = self.card.inner
        inner.configure(bg=theme.SURFACE)

        NeumoCardTitle(inner, icon_name="bolt", title="Clicker").pack(
            fill="x", pady=(0, 2)
        )

        self._gauge = NeumoGauge(
            inner, value=0, max_value=1000, label="CPS",
            width=theme.GAUGE_WIDTH, height=theme.GAUGE_HEIGHT,
        )
        self._gauge.pack(pady=(2, 0))

    def set_cps(self, value):
        self._gauge.set_value(value)


class StatusCard:
    """Left column bottom: status pill, runtime, always-on-top toggle."""

    def __init__(self, parent, app):
        self.app = app
        self.card = NeumoCard(parent, padding=theme.CARD_PADDING_TIGHT)
        self._build()

    def _build(self):
        inner = self.card.inner
        inner.configure(bg=theme.SURFACE)

        NeumoCardTitle(
            inner, icon_name="clock", title="Status",
            right_factory=lambda row: NeumoPowerDot(
                row, on=False, command=self.app.toggle_always_on_top
            ),
        ).pack(fill="x", pady=(0, 8))

        self._badge = NeumoStatusBadge(
            inner, text="IDLE", dot_color=theme.INK_MUTED
        )
        self._badge.pack(anchor="w", pady=(0, 8))

        row = tk.Frame(inner, bg=theme.SURFACE)
        row.pack(fill="x")

        self._runtime_var = tk.StringVar(value="00:00:00")
        tk.Label(
            row, textvariable=self._runtime_var,
            font=_resolve(theme.FONT_MONO_CHAIN, 12, "light"),
            bg=theme.SURFACE, fg=theme.INK_MUTED,
        ).pack(side="left")

        self._topmost_toggle = NeumoToggle(row, on_change=self.app.on_topmost_toggle)
        self._topmost_toggle.pack(side="right")
        tk.Label(
            row, text="TOP",
            font=_resolve(theme.FONT_LIGHT_CHAIN, 10, "light"),
            bg=theme.SURFACE, fg=theme.INK_MUTED,
        ).pack(side="right", padx=(0, 6))

    def set_state(self, text, dot_color):
        self._badge.set_state(text, dot_color)

    def set_runtime(self, seconds):
        h, rem = divmod(int(seconds), 3600)
        m, s = divmod(rem, 60)
        self._runtime_var.set(f"{h:02d}:{m:02d}:{s:02d}")

    def set_topmost(self, on):
        self._topmost_toggle.set(on)


class SettingsCard:
    """Right column: CPS, countdown, pause key."""

    def __init__(self, parent, app):
        self.app = app
        self.card = NeumoCard(parent, padding=theme.CARD_PADDING_TIGHT)
        self._build()

    def _build(self):
        inner = self.card.inner
        inner.configure(bg=theme.SURFACE)

        NeumoCardTitle(inner, icon_name="list", title="Settings").pack(
            fill="x", pady=(0, 8)
        )

        self.cps_entry = self._field(
            inner, "CPS", "20",
            "Clicks per second, 1 to 1000. The real rate is approximate: it "
            "depends on CPU load, the Python interpreter, and timing jitter.",
        )
        self.countdown_entry = self._field(
            inner, "Countdown", "5",
            "Seconds to wait after pressing Start before clicking begins.",
        )
        self.pause_key_entry = self._field(
            inner, "Pause key", "alt_gr",
            "pynput Key name used to pause and resume. Examples: alt_gr, "
            "ctrl_l, shift_r, f6. Press it while running to toggle pause.",
        )

    def _field(self, parent, label, default, help_text):
        row = tk.Frame(parent, bg=theme.SURFACE)
        row.pack(fill="x", pady=(0, 8))

        label_font = _resolve(theme.FONT_LIGHT_CHAIN, 10, "light")
        tk.Label(
            row, text=label.upper(), font=label_font,
            bg=theme.SURFACE, fg=theme.INK_MUTED,
        ).pack(side="left", padx=(0, 10))

        entry = NeumoSoftEntry(row, width=10)
        entry.var.set(default)
        entry.pack(side="left", fill="x", expand=True)

        help_btn = NeumoPillButton(
            row, text="?", variant="ghost", width=30, height=30,
        )
        help_btn.pack(side="left", padx=(8, 0))
        NeumoTooltip(help_btn, help_text)
        return entry

    def set_cps_invalid(self, invalid):
        self.cps_entry.set_invalid(invalid)

    def set_countdown_invalid(self, invalid):
        self.countdown_entry.set_invalid(invalid)

    def set_pause_key_invalid(self, invalid):
        self.pause_key_entry.set_invalid(invalid)


class ActionBar:
    """Bottom wide pill: Start, Stop, Quit."""

    def __init__(self, parent, app):
        self.app = app
        self.card = NeumoCard(parent, padding=theme.CARD_PADDING_TIGHT)
        self._build()

    def _build(self):
        inner = self.card.inner
        inner.configure(bg=theme.SURFACE)

        self._start = NeumoPillButton(
            inner, text="Start", variant="primary", height=36,
            with_icon="play", command=self.app.start_auto_clicker,
        )
        self._start.pack(side="left", padx=(0, 8))

        self._stop = NeumoPillButton(
            inner, text="Stop", variant="secondary", height=36,
            with_icon="power", command=self.app.stop_clicking,
        )
        self._stop.pack(side="left", padx=(0, 8))

        self._quit = NeumoPillButton(
            inner, text="Quit", variant="ghost", height=36,
            command=self.app.quit,
        )
        self._quit.pack(side="right")

    def set_running(self, running):
        self._stop.set_disabled(not running)
        self._start.set_disabled(running)


class Dashboard:
    """Two-column layout with a full-width action bar underneath."""

    def __init__(self, root, app):
        self.root = root
        self.app = app
        self._shell = tk.Frame(root, bg=theme.SURFACE)
        self._shell.pack(fill="both", expand=True, padx=OUTER_PAD, pady=OUTER_PAD)

        # Grid with equal column weights. Pack expand hands leftover space
        # out proportionally to each child's requested width, which let the
        # wide gauge card starve the settings column.
        self._columns = tk.Frame(self._shell, bg=theme.SURFACE)
        self._columns.pack(side="top", fill="x")
        self._columns.grid_columnconfigure(0, weight=1, uniform="col")
        self._columns.grid_columnconfigure(1, weight=1, uniform="col")
        self._left_col = tk.Frame(self._columns, bg=theme.SURFACE)
        self._right_col = tk.Frame(self._columns, bg=theme.SURFACE)
        self._left_col.grid(row=0, column=0, sticky="nsew",
                            padx=(0, COLUMN_GAP // 2))
        self._right_col.grid(row=0, column=1, sticky="nsew",
                             padx=(COLUMN_GAP // 2, 0))

        # Each card hugs its own content height instead of stretching to
        # fill the column, so short cards do not render as tall empty slabs.
        # The dial spans 0..1000 CPS; tick labels show the real CPS values
        # so the needle reads against the range the user actually types.
        self.dial = DialCard(self._left_col, app)
        self.dial.card.pack(side="top", fill="x", pady=(0, CARD_GAP))
        self.status = StatusCard(self._left_col, app)
        self.status.card.pack(side="top", fill="x")

        self.settings = SettingsCard(self._right_col, app)
        self.settings.card.pack(side="top", fill="x")

        # The action bar spans both columns so the three pills get room for
        # their icons without the 256px column squeezing the last one flat.
        self.actions = ActionBar(self._shell, app)
        self.actions.card.pack(side="top", fill="x", pady=(CARD_GAP, 0))

    def get_settings(self):
        return {
            "cps": self.settings.cps_entry.var.get(),
            "countdown": self.settings.countdown_entry.var.get(),
            "pause_key": self.settings.pause_key_entry.var.get(),
        }

    def set_settings(self, values):
        self.settings.cps_entry.var.set(values.get("cps", ""))
        self.settings.countdown_entry.var.set(values.get("countdown", ""))
        self.settings.pause_key_entry.var.set(values.get("pause_key", ""))

    def set_cps(self, value):
        self.dial.set_cps(value)

    def set_state(self, text, dot_color):
        self.status.set_state(text, dot_color)

    def set_runtime(self, seconds):
        self.status.set_runtime(seconds)

    def set_topmost(self, on):
        self.status.set_topmost(on)

    def set_running(self, running):
        self.actions.set_running(running)
