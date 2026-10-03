"""Compact two-column dashboard: dial and status left, settings right.

Both columns are the same height and the action bar spans the full width
underneath. Every card hugs its content, so the columns balance by design
rather than by luck.

The settings fields stack the label above the input. Beside each other in a
256px column the label and the help button consumed 150 of the 200px of
usable width and left the input about 40px, which is what made the settings
look crushed.
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

COLUMN_GAP = theme.SPACE_3
CARD_GAP = theme.SPACE_3
OUTER_PAD = theme.SPACE_4
FIELD_GAP = 12


class DialCard:
    """Left column: the CPS dial and its readout."""

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
        self._gauge.pack()

    def set_cps(self, value):
        self._gauge.set_value(value)


class StatusCard:
    """Left column: state pill, runtime, and the always-on-top switch.

    The pill and the switch share a row. Stacked, the card ran 20px past
    what the column could give it and the action bar below got clipped.
    """

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
        ).pack(fill="x", pady=(0, 10))

        top_row = tk.Frame(inner, bg=theme.SURFACE)
        top_row.pack(fill="x")

        self._badge = NeumoStatusBadge(
            top_row, text="IDLE", dot_color=theme.INK_MUTED
        )
        self._badge.pack(side="left")

        self._topmost_toggle = NeumoToggle(top_row, on_change=self.app.on_topmost_toggle)
        self._topmost_toggle.pack(side="right")
        tk.Label(
            top_row, text="TOP",
            font=_resolve(theme.FONT_LIGHT_CHAIN, 10, "light"),
            bg=theme.SURFACE, fg=theme.INK_MUTED,
        ).pack(side="right", padx=(0, 6))

        foot = tk.Frame(inner, bg=theme.SURFACE)
        foot.pack(fill="x", pady=(10, 0))

        self._runtime_var = tk.StringVar(value="00:00:00")
        tk.Label(
            foot, textvariable=self._runtime_var,
            font=_resolve(theme.FONT_MONO_CHAIN, 12, "light"),
            bg=theme.SURFACE, fg=theme.INK_MUTED,
        ).pack(side="left")

        # Which build is on screen. A screenshot alone cannot answer that.
        self._build_label = tk.Label(
            foot, text="",
            font=_resolve(theme.FONT_MONO_CHAIN, 9, "light"),
            bg=theme.SURFACE, fg=theme.INK_FAINT,
        )
        self._build_label.pack(side="right")

    def set_state(self, text, dot_color):
        self._badge.set_state(text, dot_color)

    def set_runtime(self, seconds):
        h, rem = divmod(int(seconds), 3600)
        m, s = divmod(rem, 60)
        self._runtime_var.set(f"{h:02d}:{m:02d}:{s:02d}")

    def set_topmost(self, on):
        self._topmost_toggle.set(on)

    def set_build(self, build):
        self._build_label.configure(text=build)


class SettingsCard:
    """Right column: CPS, countdown, and pause key, one field per block."""

    def __init__(self, parent, app):
        self.app = app
        self.card = NeumoCard(parent, padding=theme.CARD_PADDING_TIGHT)
        self._build()

    def _build(self):
        inner = self.card.inner
        inner.configure(bg=theme.SURFACE)

        title_row = tk.Frame(inner, bg=theme.SURFACE)
        title_row.pack(fill="x", pady=(0, 10))
        from autoclicker.ui.widgets import NeumoIcon
        NeumoIcon(title_row, name="list", with_well=False, size=20).pack(
            side="left", padx=(0, 10)
        )
        tk.Label(
            title_row, text="SETTINGS",
            font=_resolve(theme.FONT_LIGHT_CHAIN, 12, "light"),
            bg=theme.SURFACE, fg=theme.INK_STRONG,
        ).pack(side="left")

        self.cps_entry = self._field(
            inner, "CPS", "20",
            "Clicks per second, 1 to 1000. The real rate is approximate: it "
            "depends on CPU load, the Python interpreter, and timing jitter.",
        )
        self.countdown_entry = self._field(
            inner, "COUNTDOWN", "5",
            "Seconds to wait after pressing Start before clicking begins.",
        )
        self.pause_key_entry = self._field(
            inner, "PAUSE KEY", "alt_gr",
            "pynput Key name used to pause and resume. Examples: alt_gr, "
            "ctrl_l, shift_r, f6. Press it while running to toggle pause.",
        )

    def _field(self, parent, label, default, help_text):
        block = tk.Frame(parent, bg=theme.SURFACE)
        block.pack(fill="x", pady=(0, FIELD_GAP))

        # Label on its own line, then the input with the help button beside
        # it. Putting the label and the button on one line made that row as
        # tall as the button's shadow margin, wasting 38px per field.
        tk.Label(
            block, text=label,
            font=_resolve(theme.FONT_LIGHT_CHAIN, 10, "light"),
            bg=theme.SURFACE, fg=theme.INK_MUTED,
        ).pack(anchor="w", pady=(0, 5))

        line = tk.Frame(block, bg=theme.SURFACE)
        line.pack(fill="x")

        entry = NeumoSoftEntry(line, width=10)
        entry.var.set(default)
        entry.pack(side="left", fill="x", expand=True)

        help_btn = NeumoPillButton(
            line, text="?", variant="ghost", width=22, height=22, compact=True
        )
        help_btn.pack(side="right", padx=(6, 0))
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
        self.card = NeumoCard(parent, padding=8)
        self._build()

    def _build(self):
        inner = self.card.inner
        inner.configure(bg=theme.SURFACE)

        self._start = NeumoPillButton(
            inner, text="Start", variant="primary", height=40,
            with_icon="play", command=self.app.start_auto_clicker,
        )
        self._start.pack(side="left", padx=(0, 10))

        self._stop = NeumoPillButton(
            inner, text="Stop", variant="secondary", height=40,
            with_icon="power", command=self.app.stop_clicking,
        )
        self._stop.pack(side="left")

        self._quit = NeumoPillButton(
            inner, text="Quit", variant="ghost", height=40,
            command=self.app.quit,
        )
        self._quit.pack(side="right")

    def set_running(self, running):
        self._stop.set_disabled(not running)
        self._start.set_disabled(running)


class Dashboard:
    """Two equal columns with a full-width action bar underneath."""

    def __init__(self, root, app):
        self.root = root
        self.app = app
        self._shell = tk.Frame(root, bg=theme.SURFACE)
        self._shell.pack(fill="both", expand=True, padx=OUTER_PAD, pady=OUTER_PAD)

        # Grid with equal column weights. Pack expand hands leftover space
        # out proportionally to each child's requested width, which let the
        # wide dial card starve the settings column.
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

        self.dial = DialCard(self._left_col, app)
        self.dial.card.pack(side="top", fill="x", pady=(0, CARD_GAP))
        self.status = StatusCard(self._left_col, app)
        self.status.card.pack(side="top", fill="x")

        self.settings = SettingsCard(self._right_col, app)
        self.settings.card.pack(side="top", fill="x")

        # Full width so the three pills get room for their icons; in a single
        # 256px column the last one was squeezed flat.
        self.actions = ActionBar(self._shell, app)
        self.actions.card.pack(side="top", fill="x", pady=(CARD_GAP, 0))

    def set_build(self, build):
        """Show the running build in the status card."""
        self.status.set_build(build)

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
