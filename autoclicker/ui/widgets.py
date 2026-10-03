"""Reusable Neumorphic widget primitives.

No PIL and no ttk. Soft shadows are simulated by drawing concentric rounded
shapes on a Tk Canvas with color stops blending from the shadow color to the
surface color. Shadow contrast is intentionally low (3-6%) per the design
spec; the lift reads as a hint, not a stamp.

Every control paints itself on a single Canvas. ttk and child Frames were
both tried and both fought the design: ttk draws themed borders no option
removes, and a child Frame paints a hard rectangle over the rounded shape
underneath. One Canvas per control means one background, one silhouette, and
one event target, so hover and press always cover the whole button.
"""

import tkinter as tk
from math import cos as _cos, sin as _sin

from autoclicker.ui import theme


def _blend(color_a, color_b, t):
    return theme.blend(color_a, color_b, t)


def _resolve(chain, size, weight):
    return theme.resolve_font(chain, size, weight)


def _rounded(canvas, x1, y1, x2, y2, r, **kwargs):
    r = max(int(r), 1)
    # Clamp the radius so it can never exceed half the shorter side. A
    # radius past the midpoint makes the smoothing polygon self-intersect
    # and Tk renders it as a rectangle with pinched corners.
    r = min(r, int((x2 - x1) / 2), int((y2 - y1) / 2))
    r = max(r, 1)
    pts = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r,
        x2, y2, x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r,
        x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kwargs)


def _stadium(canvas, x1, y1, x2, y2, fill="", outline="", width=1):
    """Draw a true pill (fully rounded ends).

    A smoothing polygon with radius == half the height collapses into a
    rectangle. Composing two caps and a body keeps the ends round at any
    size, which is what the reference pills need.
    """
    height = y2 - y1
    r = height / 2.0
    cy = (y1 + y2) / 2.0
    return [
        canvas.create_oval(x1, cy - r, x1 + 2 * r, cy + r,
                           fill=fill, outline=outline, width=width),
        canvas.create_oval(x2 - 2 * r, cy - r, x2, cy + r,
                           fill=fill, outline=outline, width=width),
        canvas.create_rectangle(x1 + r, y1, x2 - r, y2,
                                fill=fill, outline=outline, width=width),
    ]


def draw_glyph(canvas, name, cx, cy, color, size, items=None):
    """Draw a catalog icon centred on (cx, cy) at `size` px.

    Shared by NeumoIcon and NeumoPillButton so a button's icon and a
    standalone icon are pixel-identical.
    """
    defs = ICONS.get(name, [])
    if not defs:
        return
    scale = size / float(theme.ICON_BOX)
    ox = cx - theme.ICON_BOX * scale / 2.0
    oy = cy - theme.ICON_BOX * scale / 2.0

    def px(x, y):
        return ox + x * scale, oy + y * scale

    for entry in defs:
        kind = entry[0]
        if kind == "polygon":
            pts = entry[1]
            filled = entry[2] if len(entry) == 3 else True
            coords = [c for p in pts for c in px(*p)]
            if filled:
                item = canvas.create_polygon(
                    coords, fill=color, outline=color, smooth=True
                )
            else:
                item = canvas.create_line(
                    coords, fill=color, width=theme.ICON_STROKE,
                    capstyle=tk.ROUND, joinstyle=tk.ROUND, smooth=True,
                )
        elif kind == "line":
            if len(entry) == 4:
                (x1, y1), (x2, y2), w = entry[1], entry[2], entry[3]
            else:
                x1, y1, x2, y2, w = entry[1]
            a, b = px(x1, y1), px(x2, y2)
            item = canvas.create_line(
                a[0], a[1], b[0], b[1], fill=color, width=max(w * scale, 1),
                capstyle=tk.ROUND, joinstyle=tk.ROUND,
            )
        elif kind == "circle":
            if len(entry) == 3:
                gx, gy, r = entry[1]
                filled = entry[2]
            else:
                gx, gy, r, filled = entry[1]
            x, y = px(gx, gy)
            rr = r * scale
            if filled:
                item = canvas.create_oval(
                    x - rr, y - rr, x + rr, y + rr, fill=color, outline=color
                )
            else:
                item = canvas.create_oval(
                    x - rr, y - rr, x + rr, y - rr * 0 + rr,
                    outline=color, width=max(theme.ICON_STROKE * scale, 1),
                )
        elif kind == "arc":
            if len(entry) == 3:
                gx, gy, r, start, extent = entry[1]
                w = entry[2]
            else:
                gx, gy, r, start, extent, w = entry[1]
            x, y = px(gx, gy)
            rr = r * scale
            item = canvas.create_arc(
                x - rr, y - rr, x + rr, y + rr,
                start=start, extent=extent, style=tk.ARC,
                outline=color, width=max(w * scale, 1),
            )
        else:
            continue
        if items is not None:
            items.append(item)


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
        # Nudged toward the box centre. Authored in the lower right, the
        # arrow sat off-balance inside the card title.
        ("polygon", [(10, 4), (10, 22), (14, 18), (17, 24), (19, 23),
                     (16, 17), (21, 17)], True),
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
        # Tk angles: 0 is 3 o'clock, 90 is 12 o'clock, counting
        # counterclockwise. A refresh glyph needs a gap near the top, so the
        # arc starts at 60 and sweeps 300 degrees back round to 360, and the
        # arrowhead sits at the open end. The previous start=30 extent=330
        # left the gap on the right while the arrowhead was drawn at the top.
        ("arc", (14, 14, 10, 60, 300, 2.0)),
        ("polygon", [(24, 10), (17, 7), (20, 15)], True),
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
        ("line", (11, 8), (17, 14), 2.0),
        ("line", (17, 14), (11, 20), 2.0),
    ],
    "power": [
        # A power glyph is a near-full ring with a gap at 12 o'clock (90
        # degrees) plus a stem through the gap. start=120 extent=300 leaves
        # exactly that 60 degree gap. The previous start=250 extent=70 drew
        # only a 70 degree fragment, which rendered as a stray tick.
        ("arc", (14, 15, 9, 120, 300, 2.0)),
        ("line", (14, 3, 14, 13, 2.0)),
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

    def __init__(self, parent, name="click", with_well=False, size=36,
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
        # The well already covers the full canvas, so the glyph always draws
        # at its natural size centred inside it.
        size = self._size - 10 if self._with_well else self._size
        draw_glyph(
            self, self._name, self._size / 2.0, self._size / 2.0,
            color, size, self._glyph_items,
        )


class NeumoPillButton(tk.Canvas):
    """Pill button drawn entirely on the Canvas.

    Earlier versions hosted a child Frame plus a Label. The Frame kept a
    fixed size, so its background painted a hard rectangle over the rounded
    pill and the focus ring drew as a box. Drawing the pill, icon, and text
    directly on the Canvas keeps one background, one shape, and one event
    target, so hover and press always cover the whole button.
    """

    VARIANTS = ("primary", "secondary", "danger", "ghost")

    def __init__(self, parent, text, variant="secondary", command=None,
                 width=None, height=40, font=None, with_icon=None, icon_size=16):
        self._edge = theme.SHADOW_OFFSET + 2
        if font is None:
            font = theme.font_to_tk(theme.FONT_BUTTON)
        self._font = font if hasattr(font, "measure") else _resolve(
            theme.FONT_LIGHT_CHAIN, theme.FONT_BUTTON[1], "light"
        )
        self._icon_name = with_icon
        self._icon_size = icon_size
        self._text = text
        self._variant = variant
        self._command = command
        self._height = height
        self._hover = False
        self._pressed = False
        self._focused = False
        self._disabled = False
        self._running = False

        text_w = self._font.measure(text)
        pad_x = 16
        gap = 8 if with_icon else 0
        icon_w = icon_size + gap if with_icon else 0
        needed = text_w + icon_w + pad_x * 2
        self._width = max(int(width) if width else 0, int(needed))

        super().__init__(
            parent,
            width=self._width + self._edge * 2,
            height=self._height + self._edge * 2,
            bg=theme.SURFACE,
            highlightthickness=0,
            bd=0,
            takefocus=1,
        )
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<FocusIn>", lambda _e: self.set_focused(True))
        self.bind("<FocusOut>", lambda _e: self.set_focused(False))
        self._render()

    # ---- state ----

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

    def _fg_for(self):
        if self._disabled:
            return theme.INK_FAINT
        if self._variant in ("primary", "danger"):
            return "#FFFFFF"
        if self._variant == "ghost":
            return theme.INK_MUTED
        return theme.INK_STRONG

    def _icon_color(self):
        if self._disabled:
            return theme.INK_FAINT
        if self._variant in ("primary", "danger"):
            return "#FFFFFF"
        if self._variant == "ghost":
            return theme.INK_MUTED
        return theme.INK

    # ---- paint ----

    def _render(self):
        self.delete("all")
        w, h = self._width, self._height
        x0, y0 = self._edge, self._edge
        x1, y1 = x0 + w, y0 + h
        pressed = self._pressed or (self._variant == "primary" and self._running)

        offset = theme.SHADOW_OFFSET_INNER if pressed else theme.SHADOW_OFFSET
        if self._hover and not pressed and not self._disabled:
            offset = theme.SHADOW_OFFSET + 1
        steps = theme.SHADOW_BLUR_STEPS_INNER if pressed else theme.SHADOW_BLUR_STEPS

        for i in range(steps):
            t = i / max(steps - 1, 1)
            _stadium(
                self,
                x0 - offset - i, y0 - offset - i,
                x1 + offset + i, y1 + offset + i,
                fill=_blend(theme.SHADOW_LIGHT_HEX, theme.SURFACE, t),
            )
        for i in range(steps):
            t = i / max(steps - 1, 1)
            _stadium(
                self,
                x0 + offset - i, y0 + offset - i,
                x1 + offset + i, y1 + offset + i,
                fill=_blend(theme.SHADOW_DARK_HEX, theme.SURFACE, t),
            )

        if self._focused and not self._disabled:
            _stadium(
                self,
                x0 - theme.FOCUS_RING_OFFSET, y0 - theme.FOCUS_RING_OFFSET,
                x1 + theme.FOCUS_RING_OFFSET, y1 + theme.FOCUS_RING_OFFSET,
                outline=theme.ACCENT, width=theme.FOCUS_RING_WIDTH,
            )

        fill = self._fill_for()
        _stadium(self, x0, y0, x1, y1, fill=fill)

        cy = (y0 + y1) / 2.0
        text_w = self._font.measure(self._text)
        content_w = text_w + (self._icon_size + 8 if self._icon_name else 0)
        start_x = (x0 + x1) / 2.0 - content_w / 2.0

        if self._icon_name:
            draw_glyph(
                self, self._icon_name,
                start_x + self._icon_size / 2.0, cy,
                self._icon_color(), self._icon_size,
            )
            start_x += self._icon_size + 8

        self.create_text(
            start_x, cy, text=self._text, font=self._font,
            fill=self._fg_for(), anchor="w",
        )

    # ---- public ----

    def set_text(self, text):
        self._text = text
        self._width = max(
            self._width,
            int(self._font.measure(text)) + (self._icon_size + 8 if self._icon_name else 0) + 32,
        )
        self.configure(width=self._width + self._edge * 2)
        self._render()

    def set_disabled(self, disabled):
        self._disabled = bool(disabled)
        if disabled:
            self._hover = False
            self._pressed = False
        self.configure(cursor="" if disabled else "hand2")
        self._render()

    def set_running(self, running):
        self._running = bool(running)
        self._render()

    def set_focused(self, focused):
        self._focused = bool(focused)
        self._render()

    # ---- events ----

    def _on_enter(self, _e):
        if self._disabled or self._hover:
            return
        self._hover = True
        self.configure(cursor="hand2")
        self._render()

    def _on_leave(self, _e):
        if self._disabled:
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
        if callable(self._command):
            try:
                self._command()
            except Exception:
                pass

    def _release(self, _e=None):
        if not self._pressed:
            return
        self._pressed = False
        self._render()


class NeumoSoftEntry(tk.Frame):
    """Inset pill input: a Canvas draws the well, a plain Entry holds the text.

    ttk.Entry paints a themed border of its own that no amount of
    `borderwidth=0` removes, which left a hard outline around every field.
    tk.Entry honours `relief=flat` and `highlightthickness=0`, so the well we
    draw is the only chrome the field has.
    """

    HEIGHT = 38

    def __init__(self, parent, textvariable=None, width=10, font=None,
                 invalid=False):
        if font is None:
            font = theme.font_to_tk(theme.FONT_INPUT)
        super().__init__(parent, bg=theme.SURFACE)
        self._invalid = bool(invalid)
        self._focused = False
        self._edge = theme.SHADOW_OFFSET_INNER

        # A bare Canvas reports a 378px requested width, which would starve
        # the sibling controls. Start at 1px and let fill="x" size it.
        self._canvas = tk.Canvas(
            self, bg=theme.SURFACE, highlightthickness=0, bd=0,
            width=1, height=self.HEIGHT + self._edge * 2,
        )
        self._canvas.pack(fill="x")

        self._var = textvariable or tk.StringVar()
        self._entry = tk.Entry(
            self._canvas,
            textvariable=self._var,
            width=width,
            font=font,
            bg=theme.SURFACE_SUNKEN,
            fg=theme.INK_STRONG,
            insertbackground=theme.INK_STRONG,
            selectbackground=theme.ACCENT_SOFT,
            selectforeground=theme.INK_STRONG,
            relief="flat",
            bd=0,
            highlightthickness=0,
            takefocus=1,
        )
        self._entry.bind("<FocusIn>", lambda _e: self._set_focus(True))
        self._entry.bind("<FocusOut>", lambda _e: self._set_focus(False))
        self._canvas.bind("<Configure>", lambda _e: self._render())
        self._render()

    def _set_focus(self, focused):
        self._focused = bool(focused)
        self._render()

    def set_invalid(self, invalid):
        self._invalid = bool(invalid)
        self._render()

    def set_disabled(self, disabled):
        self._entry.configure(
            state="disabled" if disabled else "normal",
            fg=theme.INK_FAINT if disabled else theme.INK_STRONG,
        )
        self._render()

    @property
    def var(self):
        return self._var

    @property
    def entry(self):
        return self._entry

    def focus(self):
        self._entry.focus_set()

    def _render(self):
        self._canvas.delete("all")
        w = self._canvas.winfo_width() or 1
        h = self.HEIGHT
        e = self._edge
        x0, y0 = e, e
        x1, y1 = w - e, h + e
        steps = theme.SHADOW_BLUR_STEPS_INNER

        # Inset: dark shadow top-left, light shadow bottom-right.
        for i in range(steps):
            t = i / max(steps - 1, 1)
            _stadium(
                self._canvas,
                x0 - e - i, y0 - e - i, x1 + e + i, y1 + e + i,
                fill=_blend(theme.SHADOW_DARK_HEX, theme.SURFACE_SUNKEN, t),
            )
        for i in range(steps):
            t = i / max(steps - 1, 1)
            _stadium(
                self._canvas,
                x0 + e - i, y0 + e - i, x1 - e + i, y1 - e + i,
                fill=_blend(theme.SHADOW_LIGHT_HEX, theme.SURFACE_SUNKEN, t),
            )

        if self._focused or self._invalid:
            ring = theme.DANGER if self._invalid else theme.ACCENT
            _stadium(
                self._canvas,
                x0 - theme.FOCUS_RING_OFFSET, y0 - theme.FOCUS_RING_OFFSET,
                x1 + theme.FOCUS_RING_OFFSET, y1 + theme.FOCUS_RING_OFFSET,
                outline=ring, width=theme.FOCUS_RING_WIDTH,
            )

        _stadium(self._canvas, x0, y0, x1, y1, fill=theme.SURFACE_SUNKEN)

        self._entry.place(
            x=x0 + 10, y=y0,
            width=max(x1 - x0 - 20, 20), height=h,
        )


class NeumoStatusBadge(tk.Canvas):
    """Inset status pill: a dot plus a label, both drawn on one Canvas.

    The previous version packed a Canvas and a Label side by side, so the
    inset pill wrapped only the dot and the label sat on the bare surface as a
    separate rectangle. One Canvas keeps the fill, the dot, and the text in the
    same shape, and the width is measured from the text so long state names are
    never clipped.
    """

    HEIGHT = 30
    DOT_R = 4
    DOT_GAP = 10
    PAD_X = 13

    def __init__(self, parent, text="IDLE", dot_color=None):
        self._text = text.upper()
        self._dot_color = dot_color or theme.INK_MUTED
        self._font = _resolve(theme.FONT_LIGHT_CHAIN, 11, "light")
        super().__init__(
            parent,
            width=self._measure(),
            height=self.HEIGHT + theme.SHADOW_OFFSET_INNER * 2 + 4,
            bg=theme.SURFACE,
            highlightthickness=0,
            bd=0,
        )
        self._render()

    def _measure(self):
        text_w = self._font.measure(self._text)
        return (
            self.PAD_X * 2 + self.DOT_R * 2 + self.DOT_GAP + text_w
            + theme.SHADOW_OFFSET_INNER * 2
        )

    def set_state(self, text, dot_color):
        self._text = str(text).upper()
        self._dot_color = dot_color
        self.configure(width=self._measure())
        self._render()

    def _render(self):
        self.delete("all")
        w = max(self.winfo_width() or self._measure(), self._measure())
        h = self.HEIGHT
        edge = theme.SHADOW_OFFSET_INNER
        x0, y0 = edge, edge
        x1, y1 = x0 + w - edge * 2, y0 + h

        for i in range(theme.SHADOW_BLUR_STEPS_INNER):
            t = i / max(theme.SHADOW_BLUR_STEPS_INNER - 1, 1)
            _stadium(
                self,
                x0 - edge - i, y0 - edge - i, x1 + edge + i, y1 + edge + i,
                fill=_blend(theme.SHADOW_DARK_HEX, theme.SURFACE_SUNKEN, t),
            )
        for i in range(theme.SHADOW_BLUR_STEPS_INNER):
            t = i / max(theme.SHADOW_BLUR_STEPS_INNER - 1, 1)
            _stadium(
                self,
                x0 + edge - i, y0 + edge - i, x1 - edge + i, y1 - edge + i,
                fill=_blend(theme.SHADOW_LIGHT_HEX, theme.SURFACE_SUNKEN, t),
            )
        _stadium(self, x0, y0, x1, y1, fill=theme.SURFACE_SUNKEN)

        cy = (y0 + y1) / 2.0
        dot_cx = x0 + self.PAD_X + self.DOT_R
        self.create_oval(
            dot_cx - self.DOT_R, cy - self.DOT_R,
            dot_cx + self.DOT_R, cy + self.DOT_R,
            fill=self._dot_color, outline="",
        )
        self.create_text(
            dot_cx + self.DOT_R + self.DOT_GAP, cy,
            text=self._text, font=self._font, fill=theme.INK_STRONG,
            anchor="w",
        )


class NeumoToggle(tk.Canvas):
    """Two-state switch: an inset track with a raised knob."""

    TRACK_W = 50
    TRACK_H = 26
    KNOB_R = 9
    KNOB_PAD = 4

    def __init__(self, parent, on_change=None):
        self._state = False
        self._hover = False
        self._on_change = on_change
        self._edge = theme.SHADOW_OFFSET + 2
        super().__init__(
            parent,
            width=self.TRACK_W + self._edge * 2,
            height=self.TRACK_H + self._edge * 2,
            bg=theme.SURFACE,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.bind("<Button-1>", self._toggle)
        self.bind("<Enter>", lambda _e: self._set_hover(True))
        self.bind("<Leave>", lambda _e: self._set_hover(False))
        self._render()

    def _set_hover(self, hover):
        self._hover = bool(hover)
        self._render()

    def _toggle(self, _e=None):
        self.set(not self._state, notify=True)

    def get(self):
        return self._state

    def set(self, value, notify=False):
        self._state = bool(value)
        self._render()
        if notify and callable(self._on_change):
            self._on_change(self._state)

    def on_change(self, callback):
        self._on_change = callback

    def _render(self):
        self.delete("all")
        w, h = self.TRACK_W, self.TRACK_H
        x0, y0 = self._edge, self._edge
        x1, y1 = x0 + w, y0 + h
        cy = (y0 + y1) / 2.0

        for i in range(theme.SHADOW_BLUR_STEPS - 2):
            t = i / max(theme.SHADOW_BLUR_STEPS - 3, 1)
            _stadium(
                self,
                x0 - theme.SHADOW_OFFSET - i, y0 - theme.SHADOW_OFFSET - i,
                x1 + theme.SHADOW_OFFSET + i, y1 + theme.SHADOW_OFFSET + i,
                fill=_blend(theme.SHADOW_LIGHT_HEX, theme.SURFACE, t),
            )
        for i in range(theme.SHADOW_BLUR_STEPS - 2):
            t = i / max(theme.SHADOW_BLUR_STEPS - 3, 1)
            _stadium(
                self,
                x0 + theme.SHADOW_OFFSET - i, y0 + theme.SHADOW_OFFSET - i,
                x1 + theme.SHADOW_OFFSET + i, y1 + theme.SHADOW_OFFSET + i,
                fill=_blend(theme.SHADOW_DARK_HEX, theme.SURFACE, t),
            )
        _stadium(self, x0, y0, x1, y1, fill=theme.SURFACE_SUNKEN)

        knob_cx = x1 - self.KNOB_R - self.KNOB_PAD if self._state else (
            x0 + self.KNOB_R + self.KNOB_PAD
        )
        knob_fill = theme.ACCENT if self._state else theme.SURFACE
        # Knob shadow: two offset discs, then the knob on top.
        for i in range(2):
            t = i / 1.0
            self.create_oval(
                knob_cx - self.KNOB_R + 1 + i, cy - self.KNOB_R + 1 + i,
                knob_cx + self.KNOB_R + 1 + i, cy + self.KNOB_R + 1 + i,
                fill=_blend(theme.SHADOW_DARK_HEX, theme.SURFACE, t), outline="",
            )
        self.create_oval(
            knob_cx - self.KNOB_R, cy - self.KNOB_R,
            knob_cx + self.KNOB_R, cy + self.KNOB_R,
            fill=knob_fill, outline="",
        )


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


class NeumoGauge(tk.Canvas):
    """Half-circle CPS dial with tick marks and an animating needle.

    Geometry notes, both of which were wrong before:
    - The sweep runs 180deg -> 270deg -> 360deg, i.e. left -> top -> right.
      Sweeping -90 -> 0 -> +90 covers the right half instead, which left the
      arc and the ticks describing two different dials.
    - Tick labels sit just outside the outer ring. At the old radius they
      fell off the canvas at the left and right extremes and rendered as
      stray dashes.
    - The value text is drawn last over a surface-coloured knockout, so the
      needle reads as passing behind the number the way it does in the
      reference image.
    """

    LABEL_RADIUS = 82
    NEEDLE_REACH = 42
    VALUE_SIZE = 26
    SUB_SIZE = 9

    def __init__(self, parent, value=0, max_value=1000, label="CPS",
                 width=None, height=None):
        width = width or theme.GAUGE_WIDTH
        height = height or theme.GAUGE_HEIGHT
        self._w = width
        self._h = height
        self._cx = width / 2.0
        self._cy = height - 18
        self._value = 0
        self._target = 0
        self._max = max(1, max_value)
        self._label = label
        self._animation_after = None
        self._value_font = _resolve(theme.FONT_MONO_CHAIN, self.VALUE_SIZE, "light")
        self._sub_font = _resolve(theme.FONT_LIGHT_CHAIN, self.SUB_SIZE, "light")
        self._tick_font = _resolve(theme.FONT_LIGHT_CHAIN, 9, "light")
        super().__init__(
            parent, width=width, height=height,
            bg=theme.SURFACE, highlightthickness=0, bd=0,
        )
        self.set_value(value)

    # ---- angles ----

    def _sweep(self, value):
        """Map a value onto a Tk canvas angle.

        Tk puts 0deg at 3 o'clock and counts counterclockwise, so on a
        canvas (where y grows downward) 90deg is 12 o'clock and 180deg is
        9 o'clock. A top half-dial therefore runs 180deg -> 90deg -> 0deg.
        Sweeping the other way draws the bottom half, which is what the
        first version did and why the arc sat under the pivot while the
        ticks went over the top.
        """
        fraction = 0.0 if self._max == 0 else value / float(self._max)
        fraction = max(0.0, min(1.0, fraction))
        return 180 - fraction * 180

    def _point(self, angle_deg, radius):
        rad = angle_deg * 3.141592653589793 / 180.0
        return (
            self._cx + radius * _cos(rad),
            self._cy - radius * _sin(rad),
        )

    # ---- public ----

    def set_value(self, value):
        self._target = max(0, min(float(value), self._max))
        if self._animation_after is None:
            self._animate()

    # ---- paint ----

    def _paint(self):
        import math
        self.delete("all")
        cx, cy = self._cx, self._cy
        outer = theme.GAUGE_OUTER_R
        inner = theme.GAUGE_INNER_R

        # Dial rings. start=0 extent=180 draws right -> top -> left.
        for radius in (outer, inner):
            self.create_arc(
                cx - radius, cy - radius, cx + radius, cy + radius,
                start=0, extent=180, style=tk.ARC,
                outline=theme.INK_FAINT, width=1,
            )

        # Ticks and labels.
        count = theme.GAUGE_TICK_COUNT
        for i in range(count):
            angle = 180 - (i / float(count - 1)) * 180
            is_major = i in (0, (count - 1) // 2, count - 1)
            x1, y1 = self._point(angle, outer)
            x2, y2 = self._point(angle, outer - (12 if is_major else 6))
            self.create_line(
                x1, y1, x2, y2,
                fill=theme.INK if is_major else theme.INK_FAINT,
                width=1.6 if is_major else 1.0,
            )
            if is_major:
                lx, ly = self._point(angle, self.LABEL_RADIUS)
                self.create_text(
                    lx, ly,
                    text=str(int(round(i / float(count - 1) * self._max))),
                    font=self._tick_font, fill=theme.INK_MUTED,
                )

        # Active arc up to the current value.
        if self._value > 0:
            self.create_arc(
                cx - inner, cy - inner, cx + inner, cy + inner,
                start=0, extent=max(self._sweep(self._value), 0.01),
                style=tk.ARC, outline=theme.ACCENT, width=2,
            )

        # Needle: pivot -> tip, with a dot on each end.
        angle = self._sweep(self._value)
        nx, ny = self._point(angle, self.NEEDLE_REACH)
        self.create_line(
            cx, cy, nx, ny, fill=theme.ACCENT, width=2.4, capstyle=tk.ROUND
        )
        self.create_oval(
            nx - 3, ny - 3, nx + 3, ny + 3, fill=theme.ACCENT, outline=""
        )
        self.create_oval(
            cx - 5, cy - 5, cx + 5, cy + 5,
            fill=theme.ACCENT, outline=theme.SURFACE, width=2,
        )

        # Value last, over a surface knockout so the needle passes behind it.
        text = f"{int(round(self._value))}"
        value_y = cy - 28
        half_w = self._value_font.measure(text) / 2.0 + 8
        half_h = self.VALUE_SIZE * 0.75
        self.create_rectangle(
            cx - half_w, value_y - half_h, cx + half_w, value_y + half_h,
            fill=theme.SURFACE, outline="",
        )
        self.create_text(
            cx, value_y, text=text, font=self._value_font, fill=theme.INK_STRONG
        )

    # ---- animation ----

    def _animate(self):
        delta = self._target - self._value
        if abs(delta) < 0.5:
            self._value = self._target
            self._paint()
            self._animation_after = None
            return
        self._value += delta * 0.25
        self._paint()
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


class NeumoCardTitle(tk.Frame):
    """Card title row: icon on the left, tracked title, optional right action.

    The right-hand control is built by a factory that receives this row as
    its parent. Passing a pre-built widget is impossible: Tk widgets have one
    permanent parent, and the previous version destroyed and rebuilt the
    passed widget, which silently dropped its state and its bindings.
    """

    def __init__(self, parent, icon_name, title, right_factory=None):
        super().__init__(parent, bg=theme.SURFACE)
        self._icon = NeumoIcon(self, name=icon_name, with_well=False, size=20)
        self._icon.pack(side="left", padx=(0, 10))
        tk.Label(
            self,
            text=title.upper(),
            font=_resolve(theme.FONT_LIGHT_CHAIN, 12, "light"),
            bg=theme.SURFACE,
            fg=theme.INK_STRONG,
        ).pack(side="left")
        self._right = None
        if right_factory is not None:
            self._right = right_factory(self)
            self._right.pack(side="right")
