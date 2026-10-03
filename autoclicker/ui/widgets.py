"""Reusable Neumorphic widget primitives.

No PIL. Soft shadows are simulated by drawing concentric rounded rectangles
on a Tk Canvas with color stops blending from the shadow color to the
surface color. Shadow contrast is intentionally low (3-6%) per the design
spec; the lift reads as a hint, not a stamp.

Each widget is a thin wrapper around Tk Frame / Canvas / ttk so the look
matches the reference image while keeping native keyboard, focus, and
event semantics.
"""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from autoclicker.ui import theme


def _blend(color_a, color_b, t):
    return theme.blend(color_a, color_b, t)


def _resolve(chain, size, weight):
    return theme.resolve_font(chain, size, weight)


def _rounded(canvas, x1, y1, x2, y2, r, **kwargs):
    r = max(int(r), 1)
    pts = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r,
        x2, y2, x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r,
        x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kwargs)


def _draw_soft_shadow(canvas, width, height, radius, offset, pressed=False):
    """Draw a fake-blurred dual shadow around an area of `width`x`height`."""
    steps = theme.SHADOW_BLUR_STEPS if not pressed else theme.SHADOW_BLUR_STEPS_INNER
    steps = max(steps, 3)
    base_offset = offset if not pressed else theme.SHADOW_OFFSET_INNER
    # Light shadow: top-left.
    for i in range(steps):
        t = i / max(steps - 1, 1)
        color = _blend(theme.SHADOW_LIGHT_HEX, theme.SURFACE, t)
        pad = i
        x1 = -base_offset - pad
        y1 = -base_offset - pad
        x2 = width + base_offset + pad
        y2 = height + base_offset + pad
        _rounded(canvas, x1, y1, x2, y2, radius + pad, fill=color, outline="")
    # Dark shadow: bottom-right.
    for i in range(steps):
        t = i / max(steps - 1, 1)
        color = _blend(theme.SHADOW_DARK_HEX, theme.SURFACE, t)
        pad = i
        x1 = base_offset - pad
        y1 = base_offset - pad
        x2 = width + base_offset + pad
        y2 = height + base_offset + pad
        _rounded(canvas, x1, y1, x2, y2, radius + pad, fill=color, outline="")
    # Surface.
    _rounded(canvas, 0, 0, width, height, radius, fill=theme.SURFACE, outline="")


class NeumoCard(tk.Frame):
    """A raised Neumorphic surface that hosts other widgets.

    Structure: a Canvas sits behind the content purely to paint the dual
    shadow and the surface fill. The content is a normal Frame, so Tk's
    geometry manager reports a correct requested size and the card hugs
    its content instead of falling back to a Canvas default height.
    """

    def __init__(self, parent, padding=theme.CARD_PADDING, radius=theme.CARD_RADIUS,
                 **kwargs):
        kwargs.setdefault("bg", theme.SURFACE)
        super().__init__(parent, **kwargs)
        self._padding = padding
        self._radius = radius
        self._edge = theme.SHADOW_OFFSET + 2

        self._shadow = tk.Canvas(
            self, bg=theme.SURFACE, highlightthickness=0, bd=0,
            width=1, height=1,
        )
        self._shadow.place(x=0, y=0, relwidth=1.0, relheight=1.0)

        self._inner_frame = tk.Frame(
            self, bg=theme.SURFACE, padx=padding, pady=padding,
        )
        self._inner_frame.pack(fill="both", expand=True)

        self.bind("<Configure>", self._on_resize)

    @property
    def inner(self):
        return self._inner_frame

    def _on_resize(self, _event=None):
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1 or h <= 1:
            return
        self._shadow.delete("shadow")
        _draw_soft_shadow(
            self._shadow, w, h, self._radius, theme.SHADOW_OFFSET
        )


# -------- Icon catalog --------

ICONS = {
    "click": [
        ("polygon", [(14, 5), (14, 23), (18, 19), (21, 25), (23, 24),
                     (20, 18), (25, 18)], True),
    ],
    "clock": [
        ("circle", (14, 14, 10), False),
        ("line", (14, 6), (14, 10), 2.0),
        ("line", (14, 14), (19, 14), 2.0),
    ],
    "key": [
        ("circle", (8, 14, 4), False),
        ("line", (12, 14), (24, 14), 2.0),
        ("line", (20, 14), (20, 18), 2.0),
        ("line", (24, 14), (24, 18), 2.0),
    ],
    "list": [
        ("circle", (4, 9, 1.2), True),
        ("circle", (4, 14, 1.2), True),
        ("circle", (4, 19, 1.2), True),
        ("line", (6, 9), (22, 9), 2.0),
        ("line", (6, 14), (22, 14), 2.0),
        ("line", (6, 19), (22, 19), 2.0),
    ],
    "play": [
        ("polygon", [(8, 6), (8, 22), (22, 14)], True),
    ],
    "save": [
        ("polygon", [(5, 5), (23, 5), (23, 21), (5, 21)], True),
        ("polygon", [(17, 5), (23, 5), (23, 11)], True),
        ("polygon", [(9, 15), (19, 15), (19, 21), (9, 21)], True),
    ],
    "trash": [
        ("line", (5, 8), (23, 8), 2.0),
        ("line", (12, 6), (16, 6), 2.0),
        ("polygon", [(7, 9), (21, 9), (20, 21), (8, 21)], True),
        ("line", (12, 11), (12, 19), 1.5),
        ("line", (16, 11), (16, 19), 1.5),
    ],
    "capture": [
        ("circle", (14, 14, 8), False),
        ("line", (14, 4), (14, 8), 2.0),
        ("line", (14, 20), (14, 24), 2.0),
        ("line", (4, 14), (8, 14), 2.0),
        ("line", (20, 14), (24, 14), 2.0),
        ("line", (6, 6), (10, 6), 2.0),
        ("line", (6, 6), (6, 10), 2.0),
        ("line", (22, 6), (18, 6), 2.0),
        ("line", (22, 6), (22, 10), 2.0),
        ("line", (6, 22), (10, 22), 2.0),
        ("line", (6, 22), (6, 18), 2.0),
        ("line", (22, 22), (18, 22), 2.0),
        ("line", (22, 22), (22, 18), 2.0),
    ],
    "loop": [
        ("arc", (14, 14, 9, 30, 330, 2.0)),
        ("polygon", [(22, 5), (24, 11), (18, 11)], True),
    ],
    "scroll": [
        ("polygon", [(10, 4), (18, 4), (18, 24), (10, 24)], True),
        ("circle", (14, 10, 1.4), True),
        ("line", (4, 10), (7, 10), 1.5),
        ("line", (4, 14), (7, 14), 1.5),
        ("line", (21, 16), (24, 16), 1.5),
    ],
    "bolt": [
        ("polygon", [(14, 3), (8, 15), (13, 15), (11, 25), (20, 12), (15, 12)], True),
    ],
    "snow": [
        ("line", (14, 4), (14, 24), 2.0),
        ("line", (5, 9), (23, 19), 2.0),
        ("line", (5, 19), (23, 9), 2.0),
    ],
    "chevron-right": [
        ("line", (12, 8), (18, 14), 2.0),
        ("line", (18, 14), (12, 20), 2.0),
    ],
    "power": [
        ("arc", (14, 16, 7, 250, 70, 2.0)),
        ("line", (14, 6, 14, 14, 2.0)),
    ],
    "chevron-up": [
        ("line", (8, 12), (14, 6), 2.0),
        ("line", (14, 6), (20, 12), 2.0),
    ],
    "chevron-down": [
        ("line", (8, 16), (14, 22), 2.0),
        ("line", (14, 22), (20, 16), 2.0),
    ],
    "plus": [
        ("line", (14, 7), (14, 21), 2.0),
        ("line", (7, 14), (21, 14), 2.0),
    ],
    "check": [
        ("line", (7, 14), (12, 19), 2.0),
        ("line", (12, 19), (21, 9), 2.0),
    ],
    "x": [
        ("line", (10, 10), (18, 18), 2.0),
        ("line", (18, 10), (10, 18), 2.0),
    ],
    "arrow-right": [
        ("line", (6, 14), (22, 14), 2.0),
        ("line", (22, 14), (16, 8), 2.0),
        ("line", (22, 14), (16, 20), 2.0),
    ],
    "mouse": [
        ("polygon", [(10, 4), (18, 4), (18, 24), (10, 24)], True),
        ("line", (10, 12), (18, 12), 1.5),
    ],
    "calendar": [
        ("polygon", [(5, 7), (23, 7), (23, 23), (5, 23)], True),
        ("line", (5, 12), (23, 12), 1.5),
        ("line", (9, 5), (9, 9), 1.5),
        ("line", (19, 5), (19, 9), 1.5),
    ],
}


class NeumoIcon(tk.Canvas):
    """Line-art icon drawn from the ICONS catalog. Optional small neumo well."""

    def __init__(self, parent, name="click", with_well=False, size=theme.ICON_WELL,
                 accent=False, on_click=None):
        canvas_size = size if with_well else theme.ICON_BOX
        super().__init__(
            parent,
            width=canvas_size,
            height=canvas_size,
            bg=theme.SURFACE,
            highlightthickness=0,
            bd=0,
        )
        self._name = name
        self._with_well = with_well
        self._size = canvas_size
        self._accent = accent
        self._disabled = False
        self._hover = False
        self._on_click = on_click
        self._glyph_items = []
        self._well_items = []
        self.bind("<Configure>", lambda _e: self._render())
        if on_click is not None:
            self.bind("<Button-1>", self._handle_click)
            self.configure(cursor="hand2")

    def set(self, name, accent=False):
        self._name = name
        self._accent = accent
        self._render()

    def set_disabled(self, disabled):
        self._disabled = bool(disabled)
        self._render()

    def set_hover(self, hover):
        self._hover = bool(hover)
        self._render()

    def _handle_click(self, _e):
        if self._disabled:
            return
        if self._on_click is not None:
            self._on_click()

    def _render(self):
        self.delete("all")
        self._glyph_items = []
        self._well_items = []
        if self._with_well:
            self._draw_well()
        color = (
            theme.ICON_COLOR_ACCENT if self._accent
            else theme.ICON_COLOR_ACTIVE if self._hover
            else theme.ICON_COLOR_DISABLED if self._disabled
            else theme.ICON_COLOR
        )
        self._draw_glyph(color)

    def _draw_well(self):
        size = self._size
        offset = 3
        steps = 4
        for i in range(steps):
            t = i / max(steps - 1, 1)
            color = _blend(theme.SHADOW_LIGHT_HEX, theme.SURFACE, t)
            pad = i
            _rounded(
                self,
                -offset - pad, -offset - pad,
                size + offset + pad, size + offset + pad,
                size // 2 + pad, fill=color, outline="",
            )
        for i in range(steps):
            t = i / max(steps - 1, 1)
            color = _blend(theme.SHADOW_DARK_HEX, theme.SURFACE, t)
            pad = i
            _rounded(
                self,
                offset - pad, offset - pad,
                size + offset + pad, size + offset + pad,
                size // 2 + pad, fill=color, outline="",
            )
        r = size // 2
        self._well_items.append(
            self.create_oval(2, 2, size - 2, size - 2,
                              fill=theme.SURFACE, outline="")
        )

    def _draw_glyph(self, color):
        defs = ICONS.get(self._name, [])
        if not defs:
            return
        # Center the 28x28 glyph in the canvas. If there's a well, offset
        # inside the well; otherwise the canvas is 28x28 and coords are direct.
        if self._with_well:
            ox = (self._size - theme.ICON_BOX) // 2
            oy = (self._size - theme.ICON_BOX) // 2
        else:
            ox, oy = 0, 0
        for entry in defs:
            kind = entry[0]
            if kind == "polygon":
                # Accept either (pts, filled) or (pts,) where filled is implied True.
                if len(entry) == 3:
                    pts, filled = entry[1], entry[2]
                else:
                    pts, filled = entry[1], True
                pts = [(x + ox, y + oy) for x, y in pts]
                if filled:
                    self._glyph_items.append(
                        self.create_polygon(pts, fill=color, outline=color, smooth=True)
                    )
                else:
                    self._glyph_items.append(
                        self.create_line(pts, fill=color, width=theme.ICON_STROKE,
                                          capstyle=tk.ROUND, joinstyle=tk.ROUND)
                    )
            elif kind == "line":
                # Accept either ((x1, y1), (x2, y2), w) or ((x1, y1, x2, y2, w),)
                if len(entry) == 4:
                    x1, y1 = entry[1]
                    x2, y2 = entry[2]
                    w = entry[3]
                else:
                    x1, y1, x2, y2, w = entry[1]
                self._glyph_items.append(
                    self.create_line(
                        x1 + ox, y1 + oy, x2 + ox, y2 + oy,
                        fill=color, width=w, capstyle=tk.ROUND, joinstyle=tk.ROUND,
                    )
                )
            elif kind == "circle":
                # Accept either ((cx, cy, r), filled) or ((cx, cy, r, filled),)
                if len(entry) == 3:
                    cx, cy, r = entry[1]
                    filled = entry[2]
                else:
                    cx, cy, r, filled = entry[1]
                if filled:
                    self._glyph_items.append(
                        self.create_oval(
                            cx + ox - r, cy + oy - r,
                            cx + ox + r, cy + oy + r,
                            fill=color, outline=color,
                        )
                    )
                else:
                    self._glyph_items.append(
                        self.create_oval(
                            cx + ox - r, cy + oy - r,
                            cx + ox + r, cy + oy + r,
                            outline=color, width=theme.ICON_STROKE,
                        )
                    )
            elif kind == "arc":
                if len(entry) == 3:
                    cx, cy, r, start, extent = entry[1]
                    w = entry[2]
                else:
                    cx, cy, r, start, extent, w = entry[1]
                self._glyph_items.append(
                    self.create_arc(
                        cx + ox - r, cy + oy - r,
                        cx + ox + r, cy + oy + r,
                        start=start, extent=extent,
                        style=tk.ARC, outline=color, width=w,
                    )
                )


class NeumoPillButton(tk.Canvas):
    """Pill button with primary/secondary/danger/ghost variants.

    Hover and click events bind on the Canvas itself so the visual
    feedback covers the whole button, not just the inner label area.
    """

    VARIANTS = ("primary", "secondary", "danger", "ghost")

    def __init__(self, parent, text, variant="secondary", command=None,
                 width=120, height=40, font=None, with_icon=None, icon_size=18):
        pad = theme.SHADOW_OFFSET + 2
        if font is None:
            font = theme.FONT_BUTTON
        if isinstance(font, tuple) and len(font) == 3 and isinstance(font[0], tuple):
            font = theme.font_to_tk(font)
        super().__init__(
            parent,
            width=width + pad * 2,
            height=height + pad * 2,
            bg=theme.SURFACE,
            highlightthickness=0,
            bd=0,
        )
        self._label_text = text
        self._variant = variant
        self._command = command
        self._width = width
        self._height = height
        self._hover = False
        self._pressed = False
        self._focused = False
        self._disabled = False
        self._running = False
        self._font = font
        self._icon_name = with_icon
        self._icon_size = icon_size

        self._pad = pad
        self._inner = tk.Frame(self, bg=theme.SURFACE)
        self._inner.place(x=pad, y=pad, width=width, height=height)
        # Keep the frame at the requested pill size; the children are centered
        # inside it by pack.
        self._inner.pack_propagate(False)
        content = tk.Frame(self._inner, bg=theme.SURFACE)
        content.pack(expand=True, padx=0, pady=0)
        if with_icon:
            self._icon_widget = NeumoIcon(content, name=with_icon, with_well=False,
                                          size=icon_size)
            self._icon_widget.pack(side="left", padx=(0, 8))
        self._label = tk.Label(
            content,
            text=text,
            font=font,
            bg=theme.SURFACE,
            fg=self._fg_for("default"),
        )
        self._label.pack(side="left")
        # Bind hover/click on the Canvas AND every child so the visual state
        # is identical no matter which pixel of the pill the pointer is on.
        # Without child bindings, hovering the label fires <Leave> on the
        # Canvas and the highlight flickers off.
        targets = [self, self._inner, self._label]
        if with_icon:
            targets.append(self._icon_widget)
        for target in targets:
            target.bind("<Enter>", self._on_enter, add="+")
            target.bind("<Leave>", self._on_leave, add="+")
            target.bind("<Button-1>", self._on_click, add="+")
        self.bind("<ButtonRelease-1>", self._release, add="+")
        self._hover_targets = targets
        self.bind("<Configure>", lambda _e: self._render())
        self._render()

    def _fg_for(self, _state):
        if self._variant == "primary":
            return theme.SURFACE
        if self._variant == "danger":
            return theme.SURFACE
        if self._variant == "ghost":
            return theme.INK_MUTED
        return theme.INK_STRONG

    def _fill_for(self):
        if self._disabled:
            return theme.SURFACE
        if self._variant == "primary":
            return theme.ACCENT
        if self._variant == "danger":
            return theme.DANGER
        if self._pressed:
            return theme.SURFACE_SUNKEN
        if self._hover:
            return theme.SURFACE_HOVER
        return theme.SURFACE

    def _render(self):
        self.delete("all")
        w, h = self._width, self._height
        r = h // 2
        pressed = self._pressed or (self._variant == "primary" and self._running)

        offset = theme.SHADOW_OFFSET if not pressed else theme.SHADOW_OFFSET_INNER
        steps = theme.SHADOW_BLUR_STEPS if not pressed else theme.SHADOW_BLUR_STEPS_INNER
        # Stronger hover: lift the offset by 1px so the shadow grows.
        if self._hover and not self._pressed and not self._disabled:
            offset = theme.SHADOW_OFFSET + 1
            steps = theme.SHADOW_BLUR_STEPS

        for i in range(steps):
            t = i / max(steps - 1, 1)
            color = _blend(theme.SHADOW_LIGHT_HEX, theme.SURFACE, t)
            pad = i
            _rounded(
                self,
                self._pad - offset - pad, self._pad - offset - pad,
                self._pad - offset - pad + w + 2 * pad,
                self._pad - offset - pad + h + 2 * pad,
                r + pad, fill=color, outline="",
            )
        for i in range(steps):
            t = i / max(steps - 1, 1)
            color = _blend(theme.SHADOW_DARK_HEX, theme.SURFACE, t)
            pad = i
            _rounded(
                self,
                self._pad + offset - pad, self._pad + offset - pad,
                self._pad + offset - pad + w + 2 * pad,
                self._pad + offset - pad + h + 2 * pad,
                r + pad, fill=color, outline="",
            )

        if self._focused and not self._disabled:
            _rounded(
                self,
                self._pad - theme.FOCUS_RING_OFFSET,
                self._pad - theme.FOCUS_RING_OFFSET,
                self._pad + w + theme.FOCUS_RING_OFFSET,
                self._pad + h + theme.FOCUS_RING_OFFSET,
                r + theme.FOCUS_RING_OFFSET,
                outline=theme.ACCENT,
                width=theme.FOCUS_RING_WIDTH,
            )

        fill = self._fill_for()
        _rounded(self, self._pad, self._pad, self._pad + w, self._pad + h,
                 r, fill=fill, outline="")
        self._inner.configure(bg=fill)
        fg = theme.INK_FAINT if self._disabled else self._fg_for("default")
        self._label.configure(bg=fill, fg=fg)
        if self._icon_name:
            self._icon_widget._render()

    def set_text(self, text):
        self._label_text = text
        self._label.configure(text=text)

    def set_disabled(self, disabled):
        self._disabled = bool(disabled)
        if disabled:
            self._hover = False
            self._pressed = False
        self._render()

    def set_running(self, running):
        self._running = bool(running)
        self._render()

    def set_focused(self, focused):
        self._focused = bool(focused)
        self._render()

    def _on_enter(self, _e):
        if self._disabled:
            return
        if self._hover:
            return
        self._hover = True
        self.configure(cursor="hand2")
        self._render()

    def _on_leave(self, _e):
        if self._disabled:
            return
        if not self._hover:
            return
        # A <Leave> on a child fires while the pointer is still on the pill.
        # Confirm the pointer is actually outside before clearing the state.
        try:
            x = self.winfo_pointerx()
            y = self.winfo_pointery()
            inside = (
                self.winfo_rootx() <= x < self.winfo_rootx() + self.winfo_width()
                and self.winfo_rooty() <= y < self.winfo_rooty() + self.winfo_height()
            )
        except Exception:
            inside = False
        if inside:
            return
        self._hover = False
        self._pressed = False
        self.configure(cursor="")
        self._render()

    def _on_click(self, _e):
        if self._disabled:
            return
        self._pressed = True
        self._render()
        self.after(120, self._release)
        if callable(self._command):
            try:
                self._command()
            except Exception:
                pass

    def _release(self):
        self._pressed = False
        self._render()


class NeumoSoftEntry(tk.Frame):
    """Pressed-in pill input with focus ring."""

    def __init__(self, parent, textvariable=None, width=20, font=None,
                 invalid=False):
        if font is None:
            font = theme.FONT_INPUT
        if isinstance(font, tuple) and len(font) == 3 and isinstance(font[0], tuple):
            font = theme.font_to_tk(font)
        super().__init__(parent, bg=theme.SURFACE)
        self._invalid = invalid
        self._focused = False
        self._pad = theme.SHADOW_OFFSET_INNER + 1

        # Tk Canvas defaults to 378px wide. Set a small width so this
        # widget can shrink inside a packed row; fill="x" expands it.
        self._canvas = tk.Canvas(
            self, bg=theme.SURFACE, highlightthickness=0, bd=0,
            width=1, height=44,
        )
        self._canvas.pack(fill="x")

        self._style_name = "SoftEntry"
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
        try:
            base_layout = style.layout("TEntry")
        except Exception:
            base_layout = None
        if base_layout:
            style.layout(self._style_name, base_layout)
        style.configure(
            self._style_name,
            fieldbackground=theme.SURFACE_SUNKEN,
            borderwidth=0,
            relief="flat",
            insertcolor=theme.INK_STRONG,
            padding=(8, 2),
        )
        style.map(
            self._style_name,
            fieldbackground=[("focus", theme.SURFACE_SUNKEN), ("disabled", theme.SURFACE)],
            foreground=[("disabled", theme.INK_FAINT)],
        )

        self._var = textvariable or tk.StringVar()
        self._entry = ttk.Entry(
            self._canvas, textvariable=self._var, width=width, font=font,
            style=self._style_name, takefocus=1,
        )
        self._entry.bind("<FocusIn>", self._on_focus_in)
        self._entry.bind("<FocusOut>", self._on_focus_out)
        self._canvas.bind("<Configure>", lambda _e: self._render())

        self._render()

    def _render(self):
        self._canvas.delete("all")
        w = self._canvas.winfo_width() or 200
        h = 40
        r = h // 2

        steps = theme.SHADOW_BLUR_STEPS_INNER
        for i in range(steps):
            t = i / max(steps - 1, 1)
            color = _blend(theme.SHADOW_DARK_HEX, theme.SURFACE_SUNKEN, t)
            pad = i
            _rounded(
                self._canvas,
                -theme.SHADOW_OFFSET_INNER - pad, -theme.SHADOW_OFFSET_INNER - pad,
                w + theme.SHADOW_OFFSET_INNER + pad,
                h + theme.SHADOW_OFFSET_INNER + pad,
                r + pad, fill=color, outline="",
            )
        for i in range(steps):
            t = i / max(steps - 1, 1)
            color = _blend(theme.SHADOW_LIGHT_HEX, theme.SURFACE_SUNKEN, t)
            pad = i
            _rounded(
                self._canvas,
                theme.SHADOW_OFFSET_INNER - pad, theme.SHADOW_OFFSET_INNER - pad,
                w + theme.SHADOW_OFFSET_INNER + pad,
                h + theme.SHADOW_OFFSET_INNER + pad,
                r + pad, fill=color, outline="",
            )

        if self._focused or self._invalid:
            ring = theme.DANGER if self._invalid else theme.ACCENT
            _rounded(
                self._canvas,
                -theme.FOCUS_RING_OFFSET, -theme.FOCUS_RING_OFFSET,
                w + theme.FOCUS_RING_OFFSET, h + theme.FOCUS_RING_OFFSET,
                r + theme.FOCUS_RING_OFFSET,
                outline=ring, width=theme.FOCUS_RING_WIDTH,
            )

        _rounded(self._canvas, 0, 0, w, h, r, fill=theme.SURFACE_SUNKEN, outline="")
        self._entry.place(
            x=self._pad, y=self._pad,
            width=max(w - self._pad * 2, 40), height=h - self._pad * 2,
        )

    def _on_focus_in(self, _e):
        self._focused = True
        self._render()

    def _on_focus_out(self, _e):
        self._focused = False
        self._render()

    def set_invalid(self, invalid):
        self._invalid = bool(invalid)
        self._render()

    @property
    def var(self):
        return self._var

    @property
    def entry(self):
        return self._entry


class NeumoStatusBadge(tk.Frame):
    """Inset status pill with a colored dot and label.

    The pill auto-sizes to fit the label so long state strings do not
    get clipped. The Canvas tracks the label's required width.
    """

    def __init__(self, parent, text="IDLE", dot_color=None):
        super().__init__(parent, bg=theme.SURFACE)
        self._canvas = tk.Canvas(
            self, bg=theme.SURFACE, highlightthickness=0, bd=0, height=32,
        )
        self._canvas.pack(side="left")
        self._dot_color = dot_color or theme.INK_MUTED
        self._label_var = tk.StringVar(value=text)
        self._label_font = _resolve(theme.FONT_LIGHT_CHAIN, 11, "light")
        self._label = tk.Label(
            self, textvariable=self._label_var,
            font=self._label_font, bg=theme.SURFACE_SUNKEN, fg=theme.INK_STRONG,
            padx=0, pady=0,
        )
        self._label.pack(side="left", padx=(24, 14), pady=8)
        self._canvas.bind("<Configure>", lambda _e: self._render())
        self._label.bind("<Configure>", lambda _e: self._on_label_size())
        self._render()
        self._on_label_size()

    def set_state(self, text, dot_color):
        self._label_var.set(text.upper())
        self._dot_color = dot_color
        self._on_label_size()

    def _on_label_size(self):
        # Match canvas width to label width + padding so the pill hugs text.
        w = self._label.winfo_reqwidth() + 24 + 14
        h = 32
        if w > 0:
            self._canvas.configure(width=w, height=h)
        self._render()

    def _render(self):
        self._canvas.delete("all")
        w = self._canvas.winfo_width() or 96
        h = 32
        r = h // 2
        steps = theme.SHADOW_BLUR_STEPS_INNER
        for i in range(steps):
            t = i / max(steps - 1, 1)
            color = _blend(theme.SHADOW_DARK_HEX, theme.SURFACE_SUNKEN, t)
            pad = i
            _rounded(
                self._canvas, -theme.SHADOW_OFFSET_INNER - pad,
                -theme.SHADOW_OFFSET_INNER - pad,
                w + theme.SHADOW_OFFSET_INNER + pad,
                h + theme.SHADOW_OFFSET_INNER + pad,
                r + pad, fill=color, outline="",
            )
        for i in range(steps):
            t = i / max(steps - 1, 1)
            color = _blend(theme.SHADOW_LIGHT_HEX, theme.SURFACE_SUNKEN, t)
            pad = i
            _rounded(
                self._canvas, theme.SHADOW_OFFSET_INNER - pad,
                theme.SHADOW_OFFSET_INNER - pad,
                w + theme.SHADOW_OFFSET_INNER + pad,
                h + theme.SHADOW_OFFSET_INNER + pad,
                r + pad, fill=color, outline="",
            )
        _rounded(self._canvas, 0, 0, w, h, r,
                 fill=theme.SURFACE_SUNKEN, outline="")
        cx, cy = 16, h // 2
        self._canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4,
                                  fill=self._dot_color, outline="")


class NeumoToggle(tk.Canvas):
    """Switch pill with knob."""

    def __init__(self, parent, on_change=None, width=56, height=28):
        super().__init__(
            parent,
            width=width + theme.SHADOW_OFFSET * 2 + 4,
            height=height + theme.SHADOW_OFFSET * 2 + 4,
            bg=theme.SURFACE, highlightthickness=0, bd=0,
        )
        self._width = width
        self._height = height
        self._state = False
        self._on_change = on_change
        self.bind("<Button-1>", self._toggle)
        self._render()

    def _toggle(self, _e=None):
        self._state = not self._state
        self._render()
        if callable(self._on_change):
            self._on_change(self._state)

    def get(self):
        return self._state

    def set(self, value):
        self._state = bool(value)
        self._render()

    def on_change(self, callback):
        self._on_change = callback

    def _render(self):
        self.delete("all")
        w, h = self._width, self._height
        r = h // 2
        offset = theme.SHADOW_OFFSET

        for i in range(theme.SHADOW_BLUR_STEPS - 2):
            t = i / max(theme.SHADOW_BLUR_STEPS - 3, 1)
            color = _blend(theme.SHADOW_LIGHT_HEX, theme.SURFACE, t)
            _rounded(self, -offset - i, -offset - i,
                     w + offset + i, h + offset + i, r + i,
                     fill=color, outline="")
        for i in range(theme.SHADOW_BLUR_STEPS - 2):
            t = i / max(theme.SHADOW_BLUR_STEPS - 3, 1)
            color = _blend(theme.SHADOW_DARK_HEX, theme.SURFACE, t)
            _rounded(self, offset - i, offset - i,
                     w + offset + i, h + offset + i, r + i,
                     fill=color, outline="")
        _rounded(self, 0, 0, w, h, r, fill=theme.SURFACE_SUNKEN, outline="")
        knob_r = r - 4
        cy = h // 2
        if self._state:
            cx = w - knob_r - 4
            knob_fill = theme.ACCENT
        else:
            cx = knob_r + 4
            knob_fill = theme.SURFACE
        # Tiny shadow under knob.
        for i in range(2):
            t = i / 1
            _rounded(self, cx - knob_r + 1, cy - knob_r + 1,
                     cx + knob_r + 1, cy + knob_r + 1,
                     knob_r, fill=_blend(theme.SHADOW_DARK_HEX, theme.SURFACE, t),
                     outline="")
        self.create_oval(cx - knob_r, cy - knob_r, cx + knob_r, cy + knob_r,
                          fill=knob_fill, outline="")


class NeumoSceneCard(tk.Frame):
    """Small scene-style card: 56px icon well, title, sub-label.

    Uses a Frame so the shadow is drawn on a Canvas behind the content and
    every child shares one hover/click binding target. Hover and pressed
    states are explicit: hover deepens the shadow, pressed inverts it.
    """

    def __init__(self, parent, icon_name, title, sub_label, command=None,
                 width=180, height=150):
        super().__init__(parent, bg=theme.SURFACE, width=width, height=height)
        self.pack_propagate(False)
        self._width = width
        self._height = height
        self._icon_name = icon_name
        self._title = title
        self._sub = sub_label
        self._command = command
        self._hover = False
        self._pressed = False
        self._active = False
        self._disabled = False

        pad = theme.SHADOW_OFFSET + 2
        self._canvas = tk.Canvas(
            self, width=width + pad * 2, height=height + pad * 2,
            bg=theme.SURFACE, highlightthickness=0, bd=0,
        )
        self._canvas.place(x=-pad, y=-pad)

        self._title_font = _resolve(theme.FONT_LIGHT_CHAIN, 12, "light")
        self._sub_font = _resolve(theme.FONT_LIGHT_CHAIN, 10, "light")

        body = tk.Frame(self, bg=theme.SURFACE)
        body.pack(fill="both", expand=True, padx=theme.SCENE_RADIUS,
                  pady=theme.SCENE_RADIUS)

        self._icon = NeumoIcon(body, name=icon_name, with_well=True, size=52)
        self._icon.pack(pady=(0, 8))

        self._title_lbl = tk.Label(
            body, text=self._title.upper(), font=self._title_font,
            bg=theme.SURFACE, fg=theme.INK_STRONG,
        )
        self._title_lbl.pack()
        self._sub_lbl = tk.Label(
            body, text=self._sub, font=self._sub_font,
            bg=theme.SURFACE, fg=theme.INK_MUTED,
        )
        self._sub_lbl.pack(pady=(2, 0))

        if command is not None:
            self.configure(cursor="hand2")
        self._bind_targets(self, self._canvas, body, self._icon,
                           self._title_lbl, self._sub_lbl)
        self.bind("<Configure>", lambda _e: self._render())
        self._render()

    def _bind_targets(self, *targets):
        for target in targets:
            target.bind("<Enter>", self._on_enter, add="+")
            target.bind("<Leave>", self._on_leave, add="+")
            target.bind("<Button-1>", self._on_click, add="+")
            target.bind("<ButtonRelease-1>", self._on_release, add="+")

    def set_title(self, title):
        self._title = title
        self._title_lbl.configure(text=title.upper())

    def set_sub(self, sub):
        self._sub = sub
        self._sub_lbl.configure(text=sub)

    def set_active(self, active):
        self._active = bool(active)
        self._icon.set(self._icon_name, accent=self._active)
        self._render()

    def set_disabled(self, disabled):
        self._disabled = bool(disabled)
        if disabled:
            self._hover = False
            self._pressed = False
        self._render()

    def _pointer_inside(self):
        try:
            x = self.winfo_pointerx()
            y = self.winfo_pointery()
            return (
                self.winfo_rootx() <= x < self.winfo_rootx() + self.winfo_width()
                and self.winfo_rooty() <= y < self.winfo_rooty() + self.winfo_height()
            )
        except Exception:
            return False

    def _on_enter(self, _e=None):
        if self._disabled or self._hover:
            return
        self._hover = True
        self._render()

    def _on_leave(self, _e=None):
        if self._disabled or not self._hover:
            return
        if self._pointer_inside():
            return
        self._hover = False
        self._pressed = False
        self._render()

    def _on_click(self, _e=None):
        if self._disabled or self._command is None:
            return
        self._pressed = True
        self._render()
        try:
            self._command()
        except Exception:
            pass

    def _on_release(self, _e=None):
        if not self._pressed:
            return
        self._pressed = False
        self._render()

    def _render(self):
        self._canvas.delete("all")
        w, h = self._width, self._height
        offset = theme.SHADOW_OFFSET
        steps = theme.SHADOW_BLUR_STEPS
        if self._hover and not self._disabled:
            offset = theme.SHADOW_OFFSET + 1
        if self._pressed:
            offset = theme.SHADOW_OFFSET_INNER
            steps = theme.SHADOW_BLUR_STEPS_INNER
        for i in range(steps):
            t = i / max(steps - 1, 1)
            color = _blend(theme.SHADOW_LIGHT_HEX, theme.SURFACE, t)
            pad = i
            _rounded(
                self._canvas, -offset - pad, -offset - pad,
                w + offset + pad, h + offset + pad,
                theme.SCENE_RADIUS + pad, fill=color, outline="",
            )
        for i in range(steps):
            t = i / max(steps - 1, 1)
            color = _blend(theme.SHADOW_DARK_HEX, theme.SURFACE, t)
            pad = i
            _rounded(
                self._canvas, offset - pad, offset - pad,
                w + offset + pad, h + offset + pad,
                theme.SCENE_RADIUS + pad, fill=color, outline="",
            )
        _rounded(self._canvas, 0, 0, w, h, theme.SCENE_RADIUS,
                 fill=theme.SURFACE, outline="")


class NeumoListItem(tk.Frame):
    """Soft inner row with icon, title, sub-label, right chevron.

    Hover lightens the row and raises the shadow. Clicking reports through
    `command`. Selected and executing states draw a left accent bar.
    """

    def __init__(self, parent, icon_name, title, sub_label, command=None,
                 width=380, height=52, right_widget=None):
        super().__init__(parent, bg=theme.SURFACE, width=width, height=height)
        self.pack_propagate(False)
        self._width = width
        self._height = height
        self._icon_name = icon_name
        self._title = title
        self._sub = sub_label
        self._command = command
        self._selected = False
        self._executing = False
        self._hover = False
        self._pressed = False

        pad = theme.SHADOW_OFFSET + 2
        self._canvas = tk.Canvas(
            self, width=width + pad * 2, height=height + pad * 2,
            bg=theme.SURFACE, highlightthickness=0, bd=0,
        )
        self._canvas.place(x=-pad, y=-pad)

        self._title_font = _resolve(theme.FONT_LIGHT_CHAIN, 11, "light")
        self._sub_font = _resolve(theme.FONT_LIGHT_CHAIN, 10, "light")

        body = tk.Frame(self, bg=theme.SURFACE)
        body.pack(fill="both", expand=True, padx=14, pady=theme.SHADOW_OFFSET + 1)

        self._icon = NeumoIcon(body, name=icon_name, with_well=True, size=32)
        self._icon.pack(side="left", padx=(0, 12))

        text_col = tk.Frame(body, bg=theme.SURFACE)
        text_col.pack(side="left", fill="x", expand=True)
        self._title_lbl = tk.Label(
            text_col, text=self._title, font=self._title_font,
            bg=theme.SURFACE, fg=theme.INK_STRONG, anchor="w",
        )
        self._title_lbl.pack(fill="x")
        self._sub_lbl = tk.Label(
            text_col, text=self._sub, font=self._sub_font,
            bg=theme.SURFACE, fg=theme.INK_MUTED, anchor="w",
        )
        self._sub_lbl.pack(fill="x", pady=(2, 0))

        if right_widget is not None:
            right_widget.pack(side="right", padx=(8, 0))
        else:
            self._chevron = NeumoIcon(body, name="chevron-right",
                                      with_well=False, size=16)
            self._chevron.pack(side="right")

        if command is not None:
            self.configure(cursor="hand2")
        self._bind_targets(self, self._canvas, body, self._icon,
                           text_col, self._title_lbl, self._sub_lbl)
        if right_widget is None:
            self._bind_targets(self._chevron)
        self.bind("<Configure>", lambda _e: self._render())
        self._render()

    def _bind_targets(self, *targets):
        for target in targets:
            target.bind("<Enter>", self._on_enter, add="+")
            target.bind("<Leave>", self._on_leave, add="+")
            target.bind("<Button-1>", self._on_click, add="+")
            target.bind("<ButtonRelease-1>", self._on_release, add="+")

    def set_title(self, title):
        self._title = title
        self._title_lbl.configure(text=title)

    def set_sub(self, sub):
        self._sub = sub
        self._sub_lbl.configure(text=sub)

    def set_selected(self, selected):
        self._selected = bool(selected)
        self._render()

    def set_executing(self, executing):
        self._executing = bool(executing)
        self._icon.set(self._icon_name,
                       accent=self._executing or self._selected)
        self._render()

    def _pointer_inside(self):
        try:
            x = self.winfo_pointerx()
            y = self.winfo_pointery()
            return (
                self.winfo_rootx() <= x < self.winfo_rootx() + self.winfo_width()
                and self.winfo_rooty() <= y < self.winfo_rooty() + self.winfo_height()
            )
        except Exception:
            return False

    def _on_enter(self, _e=None):
        if self._hover:
            return
        self._hover = True
        self._render()

    def _on_leave(self, _e=None):
        if not self._hover or self._pointer_inside():
            return
        self._hover = False
        self._pressed = False
        self._render()

    def _on_click(self, _e=None):
        self._pressed = True
        self._render()
        if self._command is not None:
            try:
                self._command()
            except Exception:
                pass

    def _on_release(self, _e=None):
        if not self._pressed:
            return
        self._pressed = False
        self._render()

    def _row_fill(self):
        if self._executing or self._selected:
            return theme.SURFACE_HOVER
        if self._pressed:
            return theme.SURFACE_SUNKEN
        if self._hover:
            return theme.SURFACE_HOVER
        return theme.SURFACE

    def _render(self):
        self._canvas.delete("all")
        w, h = self._width, self._height
        r = theme.LIST_RADIUS
        offset = 1 if not self._pressed else theme.SHADOW_OFFSET_INNER
        steps = 3 if not self._pressed else 2
        for i in range(steps):
            t = i / max(steps - 1, 1)
            color = _blend(theme.SHADOW_LIGHT_HEX, theme.SURFACE, t)
            pad = i
            _rounded(
                self._canvas, -offset - pad, -offset - pad,
                w + offset + pad, h + offset + pad,
                r + pad, fill=color, outline="",
            )
        for i in range(steps):
            t = i / max(steps - 1, 1)
            color = _blend(theme.SHADOW_DARK_HEX, theme.SURFACE, t)
            pad = i
            _rounded(
                self._canvas, offset - pad, offset - pad,
                w + offset + pad, h + offset + pad,
                r + pad, fill=color, outline="",
            )
        _rounded(self._canvas, 0, 0, w, h, r,
                 fill=self._row_fill(), outline="")
        if self._selected or self._executing:
            color = theme.SUCCESS if self._executing else theme.ACCENT
            self._canvas.create_line(2, 8, 2, h - 8, fill=color, width=2)


class NeumoPowerDot(tk.Canvas):
    """Small power indicator dot on the right of a card."""

    def __init__(self, parent, on=False, command=None, size=28):
        super().__init__(parent, width=size, height=size,
                         bg=theme.SURFACE, highlightthickness=0, bd=0)
        self._size = size
        self._on = on
        self._command = command
        self._hover = False
        if command is not None:
            self.configure(cursor="hand2")
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self._render()

    def set_on(self, on):
        self._on = bool(on)
        self._render()

    def _on_click(self, _e):
        if self._command is not None:
            try:
                self._command()
            except Exception:
                pass

    def _on_enter(self, _e):
        self._hover = True
        self._render()

    def _on_leave(self, _e):
        self._hover = False
        self._render()

    def _render(self):
        self.delete("all")
        size = self._size
        cx, cy = size // 2, size // 2
        ring_color = theme.INK if self._hover else theme.INK_FAINT
        self.create_oval(cx - 12, cy - 12, cx + 12, cy + 12,
                          outline=ring_color, width=1)
        if self._on:
            # Filled disc + glow ring.
            self.create_oval(cx - 8, cy - 8, cx + 8, cy + 8,
                              outline=theme.ACCENT, width=1)
            self.create_oval(cx - 4, cy - 4, cx + 4, cy + 4,
                              fill=theme.ACCENT, outline="")
        else:
            self.create_oval(cx - 4, cy - 4, cx + 4, cy + 4,
                              fill=theme.INK_FAINT, outline="")


class NeumoAppHeader(tk.Frame):
    """Top header with double-stroke title and right-side status pill."""

    def __init__(self, parent, title, status_pill_text="IDLE"):
        super().__init__(parent, bg=theme.SURFACE, height=72)
        self._title_canvas = tk.Canvas(
            self, height=44, bg=theme.SURFACE,
            highlightthickness=0, bd=0,
        )
        self._title_canvas.pack(side="left", padx=(32, 0), pady=14)
        self._title = title
        self._render_title()
        self._status_pill = NeumoStatusBadge(self, text=status_pill_text)
        self._status_pill.pack(side="right", padx=(0, 32), pady=24)

    def set_status(self, text, dot_color):
        if self._status_pill is not None:
            self._status_pill.set_state(text, dot_color)

    def _render_title(self):
        self._title_canvas.delete("all")
        self._title_canvas.update_idletasks()
        # Approximate width via font measure.
        font_back = _resolve(theme.FONT_LIGHT_CHAIN, 32, "light")
        font_front = font_back
        text_w = font_back.measure(self._title)
        self._title_canvas.configure(width=text_w + 4)
        self._title_canvas.create_text(
            3, 22, text=self._title, font=font_back,
            fill=theme.INK_FAINT, anchor="w",
        )
        self._title_canvas.create_text(
            2, 21, text=self._title, font=font_front,
            fill=theme.INK_STRONG, anchor="w",
        )


class NeumoGauge(tk.Canvas):
    """Half-circle gauge with tick marks and animating needle.

    Layered, drawn in this order so the value text is the visual focus:
      1. Outer + inner dial arcs (faint).
      2. Tick marks + tick labels.
      3. Active arc (accent stroke from -90 to current angle).
      4. Needle (thin line + tip dot).
      5. Pivot dot.
      6. Value text (large, monospace, INK_STRONG).
      7. Sub label (small, INK_MUTED).
    """

    def __init__(self, parent, value=0, max_value=100, label="CPS",
                 width=theme.GAUGE_WIDTH, height=theme.GAUGE_HEIGHT):
        super().__init__(
            parent, width=width, height=height,
            bg=theme.SURFACE, highlightthickness=0, bd=0,
        )
        self._width = width
        self._height = height
        self._value = 0
        self._target = value
        self._max_value = max_value
        self._label = label
        self._needle_items = []
        self._active_arc_items = []
        self._value_items = []
        self._animation_after = None
        self._set_value_instant(value)
        self.bind("<Configure>", lambda _e: self._render_static())
        self._render_static()

    def set_value(self, value):
        self._target = max(0, min(value, self._max_value))
        if self._animation_after is None:
            self._animate()

    def _set_value_instant(self, value):
        self._value = max(0, min(value, self._max_value))
        self._draw_needle()
        self._draw_value_text()
        self._draw_active_arc()

    def _angle_for(self, value):
        fraction = 0 if self._max_value == 0 else value / self._max_value
        return -90 + fraction * 180

    def _geometry(self):
        import math
        cx = self._width // 2
        cy = int(self._height * 0.78)
        return cx, cy, math

    def _draw_needle(self):
        for item in self._needle_items:
            self.delete(item)
        self._needle_items = []
        cx, cy, math = self._geometry()
        angle = self._angle_for(self._value)
        rad = angle * math.pi / 180
        # Thin needle: a line from pivot to a point near the inner ring.
        inner = theme.GAUGE_INNER_R - 14
        nx = cx + inner * math.cos(rad)
        ny = cy + inner * math.sin(rad)
        self._needle_items.append(
            self.create_line(cx, cy, nx, ny, fill=theme.ACCENT, width=2.4,
                              capstyle=tk.ROUND)
        )
        # Tip dot.
        self._needle_items.append(
            self.create_oval(nx - 3, ny - 3, nx + 3, ny + 3,
                              fill=theme.ACCENT, outline="")
        )
        # Pivot dot, drawn AFTER so it sits on top of the needle line.
        self._needle_items.append(
            self.create_oval(cx - 5, cy - 5, cx + 5, cy + 5,
                              fill=theme.ACCENT, outline=theme.SURFACE, width=2)
        )

    def _draw_active_arc(self):
        for item in self._active_arc_items:
            self.delete(item)
        self._active_arc_items = []
        if self._value <= 0:
            return
        cx, cy, _ = self._geometry()
        angle = self._angle_for(self._value)
        self._active_arc_items.append(
            self.create_arc(
                cx - theme.GAUGE_INNER_R, cy - theme.GAUGE_INNER_R,
                cx + theme.GAUGE_INNER_R, cy + theme.GAUGE_INNER_R,
                start=-90, extent=(angle + 90),
                style=tk.ARC, outline=theme.ACCENT, width=2,
            )
        )

    def _draw_value_text(self):
        for item in self._value_items:
            self.delete(item)
        self._value_items = []
        cx, cy, _ = self._geometry()
        # Value is large, above the pivot, in the dial area.
        value_font = _resolve(theme.FONT_MONO_CHAIN, 28, "light")
        sub_font = _resolve(theme.FONT_LIGHT_CHAIN, 9, "light")
        value_y = cy - 32
        self._value_items.append(
            self.create_text(cx, value_y, text=f"{int(self._value)}",
                              font=value_font, fill=theme.INK_STRONG)
        )
        self._value_items.append(
            self.create_text(cx, value_y + 22, text=self._label.upper(),
                              font=sub_font, fill=theme.INK_MUTED)
        )

    def _render_static(self):
        self.delete("all")
        cx, cy, math = self._geometry()
        # Outer arc (faint).
        self.create_arc(
            cx - theme.GAUGE_OUTER_R, cy - theme.GAUGE_OUTER_R,
            cx + theme.GAUGE_OUTER_R, cy + theme.GAUGE_OUTER_R,
            start=0, extent=180,
            style=tk.ARC, outline=theme.INK_FAINT, width=1,
        )
        # Inner arc.
        self.create_arc(
            cx - theme.GAUGE_INNER_R, cy - theme.GAUGE_INNER_R,
            cx + theme.GAUGE_INNER_R, cy + theme.GAUGE_INNER_R,
            start=0, extent=180,
            style=tk.ARC, outline=theme.INK_FAINT, width=1,
        )
        # Tick marks.
        tick_count = theme.GAUGE_TICK_COUNT
        for i in range(tick_count):
            angle = -90 + (i / (tick_count - 1)) * 180
            rad = angle * math.pi / 180
            is_major = (i == 0 or i == (tick_count - 1) // 2 or i == tick_count - 1)
            r_outer = theme.GAUGE_OUTER_R
            r_inner = (
                theme.GAUGE_OUTER_R - 12 if is_major
                else theme.GAUGE_OUTER_R - 6
            )
            x1 = cx + r_outer * math.cos(rad)
            y1 = cy + r_outer * math.sin(rad)
            x2 = cx + r_inner * math.cos(rad)
            y2 = cy + r_inner * math.sin(rad)
            color = theme.INK if is_major else theme.INK_FAINT
            width = 1.6 if is_major else 1.0
            self.create_line(x1, y1, x2, y2, fill=color, width=width)
            if is_major:
                label_val = str(int(i / (tick_count - 1) * self._max_value))
                lx = cx + (theme.GAUGE_OUTER_R + 14) * math.cos(rad)
                ly = cy + (theme.GAUGE_OUTER_R + 14) * math.sin(rad)
                tick_font = _resolve(theme.FONT_LIGHT_CHAIN, 9, "light")
                self.create_text(lx, ly, text=label_val, font=tick_font,
                                  fill=theme.INK_MUTED)
        # Re-draw the active arc, needle, and value text on top.
        self._draw_active_arc()
        self._draw_needle()
        self._draw_value_text()

    def _animate(self):
        if abs(self._value - self._target) < 0.5:
            self._value = self._target
            self._draw_needle()
            self._draw_active_arc()
            self._animation_after = None
            return
        diff = self._target - self._value
        self._value += diff * 0.25
        self._draw_needle()
        self._draw_active_arc()
        self._animation_after = self.after(16, self._animate)


class NeumoTooltip:
    """Neumorphic tooltip popover with delay-on-hover."""

    SHOW_DELAY_MS = 400
    HIDE_DELAY_MS = 100

    def __init__(self, anchor, text, variant="info", link=None, wraplength=260):
        self.anchor = anchor
        self.text = text
        self.variant = variant
        self.link = link
        self.wraplength = wraplength
        self._toplevel = None
        self._show_after = None
        self._hide_after = None
        anchor.bind("<Enter>", self._schedule_show, add="+")
        anchor.bind("<Leave>", self._schedule_hide, add="+")
        if link:
            anchor.bind("<Button-1>", self._open_link, add="+")

    def _schedule_show(self, _event=None):
        self._cancel_hide()
        if self._toplevel is not None:
            return
        self._show_after = self.anchor.after(self.SHOW_DELAY_MS, self._show)

    def _schedule_hide(self, _event=None):
        self._cancel_show()
        self._hide_after = self.anchor.after(self.HIDE_DELAY_MS, self._hide)

    def _cancel_show(self):
        if self._show_after is not None:
            try:
                self.anchor.after_cancel(self._show_after)
            except Exception:
                pass
            self._show_after = None

    def _cancel_hide(self):
        if self._hide_after is not None:
            try:
                self.anchor.after_cancel(self._hide_after)
            except Exception:
                pass
            self._hide_after = None

    def _show(self):
        self._show_after = None
        if self._toplevel is not None:
            return
        toplevel = tk.Toplevel(self.anchor)
        toplevel.wm_overrideredirect(True)
        try:
            toplevel.wm_attributes("-topmost", True)
        except Exception:
            pass

        canvas = tk.Canvas(
            toplevel, bg=theme.SURFACE, highlightthickness=0, bd=0,
            height=44, width=320,
        )
        canvas.pack(fill="both", expand=True)

        body_font = _resolve(theme.FONT_REGULAR_CHAIN, 12, "normal")
        body = tk.Label(
            toplevel, text=self.text, font=body_font,
            bg=theme.SURFACE,
            fg=theme.DANGER if self.variant == "error" else theme.INK,
            wraplength=self.wraplength, justify="left",
        )
        body_window = canvas.create_window(16, 16, window=body, anchor="nw")
        border = theme.DANGER if self.variant == "error" else ""

        def update_size(_event=None):
            canvas.configure(
                width=body.winfo_reqwidth() + 32,
                height=body.winfo_reqheight() + 32,
            )
            canvas.coords(body_window, 16, 16)
            self._draw_shadow(canvas, border=border)

        body.bind("<Configure>", update_size)
        toplevel.update_idletasks()
        update_size()

        x = self.anchor.winfo_rootx()
        y = self.anchor.winfo_rooty() + self.anchor.winfo_height() + 8
        screen_w = toplevel.winfo_screenwidth()
        screen_h = toplevel.winfo_screenheight()
        if x + 320 > screen_w:
            x = screen_w - 320 - 8
        if y + 44 > screen_h:
            y = self.anchor.winfo_rooty() - 44 - 8
        toplevel.wm_geometry(f"+{x}+{y}")

        toplevel.bind("<Enter>", self._cancel_hide)
        toplevel.bind("<Leave>", self._schedule_hide)
        self._toplevel = toplevel

    def _draw_shadow(self, canvas, border=""):
        canvas.delete("shadow")
        w = canvas.winfo_width() or 320
        h = canvas.winfo_height() or 44
        for i in range(theme.SHADOW_BLUR_STEPS - 3):
            t = i / max(theme.SHADOW_BLUR_STEPS - 4, 1)
            color = _blend(theme.SHADOW_LIGHT_HEX, theme.SURFACE, t)
            canvas.create_rectangle(-4 - i, -4 - i, w + 4 + i, h + 4 + i,
                                     fill=color, outline="", tag="shadow")
        for i in range(theme.SHADOW_BLUR_STEPS - 3):
            t = i / max(theme.SHADOW_BLUR_STEPS - 4, 1)
            color = _blend(theme.SHADOW_DARK_HEX, theme.SURFACE, t)
            canvas.create_rectangle(4 - i, 4 - i, w + 4 + i, h + 4 + i,
                                     fill=color, outline="", tag="shadow")
        r = max(theme.SMALL_RADIUS, 1)
        pts = [
            0 + r, 0, w - r, 0, w, 0, w, 0 + r, w, h - r,
            w, h, w - r, h, 0 + r, h, 0, h, 0, h - r,
            0, 0 + r, 0, 0,
        ]
        canvas.create_polygon(pts, smooth=True, fill=theme.SURFACE,
                              outline=border, width=1 if border else 0, tag="shadow")

    def _hide(self):
        self._hide_after = None
        if self._toplevel is not None:
            try:
                self._toplevel.destroy()
            except Exception:
                pass
            self._toplevel = None

    def _open_link(self, _event=None):
        if self.link:
            import webbrowser
            webbrowser.open(self.link)

    def destroy(self):
        self._hide()
        self._cancel_show()
        self._cancel_hide()


class NeumoSectionLabel(tk.Label):
    """Uppercase tracked section label."""

    def __init__(self, parent, text, **kwargs):
        kwargs.setdefault("bg", theme.SURFACE)
        kwargs.setdefault("fg", theme.INK_MUTED)
        font = kwargs.pop("font", _resolve(theme.FONT_LIGHT_CHAIN, 10, "light"))
        super().__init__(parent, text=text.upper(), font=font, **kwargs)


class NeumoCardTitle(tk.Frame):
    """Card title row: small icon on the left, title in the middle, optional action on the right."""

    def __init__(self, parent, icon_name, title, right_widget=None):
        super().__init__(parent, bg=theme.SURFACE)
        font = _resolve(theme.FONT_LIGHT_CHAIN, 12, "light")
        self._icon = NeumoIcon(self, name=icon_name, with_well=False, size=20)
        self._icon.pack(side="left", padx=(0, 10))
        tk.Label(self, text=title.upper(), font=font,
                 bg=theme.SURFACE, fg=theme.INK_STRONG).pack(side="left")
        if right_widget is not None:
            # Re-parent the right widget into this title row.
            try:
                right_widget.destroy()
            except Exception:
                pass
            new_widget = type(right_widget)(self) if False else None
            if isinstance(right_widget, NeumoPowerDot):
                new_widget = NeumoPowerDot(self, on=False,
                                            command=right_widget._command)
            elif isinstance(right_widget, NeumoPillButton):
                new_widget = NeumoPillButton(
                    self, text=right_widget._label_text,
                    variant=right_widget._variant, width=80, height=32,
                    command=right_widget._command,
                    with_icon=right_widget._icon_name,
                )
            if new_widget is not None:
                new_widget.pack(side="right")