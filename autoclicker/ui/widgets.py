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

from autoclicker.ui import render, theme


def _blend(color_a, color_b, t):
    return theme.blend(color_a, color_b, t)


def _resolve(chain, size, weight):
    return theme.resolve_font(chain, size, weight)


def _blit(canvas, image, offset=(0, 0)):
    """Blit a rendered surface and return the PhotoImage.

    A rendered surface already contains the margin its shadow needs, so it
    fills the Canvas exactly and `offset` is (0, 0) for anything that stands
    alone. Passing the margin in as the offset shifts the surface right and
    down: the shadow gets clipped on the right and bottom and the highlight
    is lost on the left and top.

    `offset` is only non-zero for an overlay, where the image is positioned so
    one specific feature lands on a chosen coordinate. Use
    render.overlay_offset for that, never a bare margin.

    Tk does not own the image buffer, so the caller must hold the returned
    object or the widget goes blank on the next garbage collect.
    """
    photo = render.to_photo(canvas, image)
    canvas.create_image(offset[0], offset[1], anchor="nw", image=photo)
    return photo


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


def _margin(depth=None, blur=None, compact=False):
    """Canvas padding needed so a rendered shadow is never clipped."""
    if compact:
        depth = render.COMPACT_DEPTH if depth is None else depth
        blur = render.COMPACT_BLUR if blur is None else blur
    depth = theme.SHADOW_DEPTH if depth is None else depth
    blur = theme.SHADOW_BLUR if blur is None else blur
    return render.margin_for(depth, blur)



class NeumoCard(tk.Frame):
    """A raised Neumorphic surface that hosts other widgets.

    A Canvas sits behind the content purely to blit the antialiased surface.
    The content is a normal Frame, so Tk's geometry manager reports a
    correct requested size and the card hugs its content rather than
    falling back to a Canvas default height.
    """

    def __init__(self, parent, padding=theme.CARD_PADDING, radius=theme.CARD_RADIUS,
                 **kwargs):
        kwargs.setdefault("bg", theme.SURFACE)
        super().__init__(parent, **kwargs)
        self._padding = padding
        self._radius = radius
        # Room for the shadow that spills past the surface.
        self._edge = _margin()

        self._shadow = tk.Canvas(
            self, bg=theme.SURFACE, highlightthickness=0, bd=0,
            width=1, height=1,
        )
        self._shadow.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self._photo = None
        self._painted = None

        # Inset by the shadow margin plus CARD_CONTENT_INSET, and taken back
        # out of the content padding. The Frame paints a flat rectangle, so
        # flush with the surface it squared off every corner and left the
        # rounded shadow around a square card. Trading the padding for the
        # inset keeps the content exactly where it was.
        self._inner_frame = tk.Frame(
            self, bg=theme.SURFACE,
            padx=max(padding - theme.CARD_CONTENT_INSET, 0),
            pady=max(padding - theme.CARD_CONTENT_INSET, 0),
        )
        self._inner_frame.pack(
            fill="both", expand=True,
            padx=self._edge + theme.CARD_CONTENT_INSET,
            pady=self._edge + theme.CARD_CONTENT_INSET,
        )

        self.bind("<Configure>", self._on_resize)

    @property
    def inner(self):
        return self._inner_frame

    def _on_resize(self, _event=None):
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1 or h <= 1:
            return
        size = (w, h)
        if size == self._painted:
            return
        self._painted = size
        self._shadow.delete("all")
        surface_w = w - self._edge * 2
        surface_h = h - self._edge * 2
        if surface_w <= 0 or surface_h <= 0:
            return
        self._photo = _blit(
            self._shadow, render.raised(surface_w, surface_h, self._radius)
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
        self._edge = _margin() if with_well else 0
        canvas_size = (size if with_well else theme.ICON_BOX) + self._edge * 2
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
        self._photo = None
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
        # Pillow blit, so the well's rim is a smooth curve rather than a
        # stepped one. The canvas reserves the shadow margin around it.
        surface = size - self._edge * 2
        if surface <= 0:
            return
        self._well_items.append(
            self.create_image(
                0, 0, anchor="nw",
                image=render.to_photo(self, render.circle(surface, well=True)),
            )
        )

    def _draw_glyph(self, color):
        # Centred on the well, not on the canvas: the canvas carries an
        # extra shadow margin on every side.
        box = self._size - self._edge * 2
        size = box - 10 if self._with_well else box
        draw_glyph(
            self, self._name,
            self._edge + box / 2.0, self._edge + box / 2.0,
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
                 width=None, height=theme.CONTROL_HEIGHT_BIG, font=None,
                 with_icon=None, icon_size=16, compact=False):
        self._compact = compact
        self._edge = _margin(compact=compact)
        if font is None:
            font = theme.font_to_tk(theme.FONT_BUTTON)
        self._font = font if hasattr(font, "measure") else _resolve(
            theme.FONT_LIGHT_CHAIN, theme.FONT_BUTTON[1], "light"
        )
        self._icon_name = with_icon
        self._icon_size = icon_size
        self._photo = None
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
        pad_x = theme.BUTTON_PAD_X_COMPACT if compact else theme.BUTTON_PAD_X
        gap = 6 if with_icon else 0
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
        self.bind("<Configure>", lambda _e: self._render())
        self._render()

    # ---- state ----

    def _fill_for(self):
        # Every pill is surface-filled, matching the reference. A solid accent
        # slab cannot read as neumorphic: against a fill darker than the
        # shadow colour the dark shadow has nowhere to go, so the button came
        # out as a flat block with a white glow around it.
        if self._disabled:
            return theme.SURFACE
        if self._pressed:
            return theme.SURFACE_SUNKEN
        if self._hover:
            return theme.SURFACE_HOVER
        return theme.SURFACE

    def _fg_for(self):
        if self._disabled:
            return theme.INK_FAINT
        if self._variant == "primary":
            return theme.ACCENT
        if self._variant == "danger":
            return theme.DANGER
        if self._variant == "ghost":
            return theme.INK_MUTED
        return theme.INK_STRONG

    def _icon_color(self):
        if self._disabled:
            return theme.INK_FAINT
        if self._variant == "primary":
            return theme.ACCENT
        if self._variant == "danger":
            return theme.DANGER
        if self._variant == "ghost":
            return theme.INK_MUTED
        return theme.INK

    # ---- paint ----

    def _render(self):
        self.delete("all")
        w, h = self._width, self._height
        x0, y0 = self._edge, self._edge
        x1, y1 = x0 + w, y0 + h
        pressed = self._pressed or self._running
        fill = self._fill_for()

        # Shape comes from Pillow: Tk cannot antialias a canvas item, so a
        # pill drawn with create_polygon has a staircase edge. The label
        # stays a canvas text item, which Xft already renders smoothly.
        # The radius is half the surface height, not a token: this button
        # takes any height and the 22px help button is not 40px.
        # The fill travels with the silhouette, not the canvas: an opaque
        # hover colour used to cover the whole canvas and the pill sat in a
        # square of it.
        ring = None
        if self._focused and not self._disabled:
            ring = (theme.ACCENT, theme.FOCUS_RING_WIDTH)
        cw, ch = self.winfo_width(), self.winfo_height()
        if cw > 1 and ch > 1:
            surface_w = cw - self._edge * 2
            surface_h = ch - self._edge * 2
            if surface_w > 0 and surface_h > 0:
                depth = render.COMPACT_DEPTH if self._compact else theme.SHADOW_DEPTH
                blur = render.COMPACT_BLUR if self._compact else theme.SHADOW_BLUR
                if pressed:
                    shape = render.inset(
                        surface_w, surface_h, surface_h // 2,
                        base=fill, ring=ring, depth=depth, blur=blur,
                    )
                else:
                    lift = 1 if (self._hover and not self._disabled) else 0
                    shape = render.raised(
                        surface_w, surface_h, surface_h // 2,
                        base=fill, lift=lift, ring=ring, depth=depth, blur=blur,
                    )
                self._photo = _blit(self, shape)

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
    """Inset pill input: a Canvas blits the well, a plain Entry holds the text.

    ttk.Entry paints a themed border of its own that `borderwidth=0` does
    not remove, so every field had a hard outline around the well. tk.Entry
    honours `relief=flat` and `highlightthickness=0`, so the blitted well is
    the only chrome the field has.
    """

    HEIGHT = theme.CONTROL_HEIGHT_MED

    def __init__(self, parent, textvariable=None, width=10, font=None,
                 invalid=False):
        if font is None:
            font = theme.font_to_tk(theme.FONT_INPUT)
        super().__init__(parent, bg=theme.SURFACE)
        self._invalid = bool(invalid)
        self._focused = False
        self._edge = _margin(theme.SHADOW_DEPTH_INNER, theme.SHADOW_BLUR_INNER)
        self._photo = None
        self._painted = None

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
        w = self._canvas.winfo_width()
        if w <= 1:
            return
        surface_w = w - self._edge * 2
        if surface_w <= 0:
            return
        state = (surface_w, self._invalid, self._focused)
        if state == self._painted:
            return
        self._painted = state

        self._canvas.delete("all")
        # The ring is part of the rasterised well, not a canvas rectangle.
        # create_rectangle drew a hard box around a pill and its corners
        # never met the well's arc.
        ring = None
        if self._focused or self._invalid:
            color = theme.DANGER if self._invalid else theme.ACCENT
            ring = (color, theme.FOCUS_RING_WIDTH)
        self._photo = _blit(
            self._canvas,
            render.inset(
                surface_w, self.HEIGHT, theme.CONTROL_RADIUS_MED, ring=ring,
            ),
        )
        self._entry.place(
            x=self._edge + 10, y=self._edge,
            width=max(surface_w - 20, 20), height=self.HEIGHT,
        )


class NeumoStatusBadge(tk.Canvas):
    """Inset status pill: a dot plus a label, both on one Canvas.

    An earlier version packed a Canvas and a Label side by side, so the
    inset pill wrapped only the dot and the text sat on the bare surface as
    a separate rectangle. One Canvas keeps the fill, the dot, and the text in
    the same shape, and the width is measured from the text so a long state
    name is never clipped.
    """

    HEIGHT = theme.STATUS_BADGE_HEIGHT
    DOT_R = theme.STATUS_BADGE_DOT_R
    DOT_GAP = theme.STATUS_BADGE_DOT_GAP
    PAD_X = theme.STATUS_BADGE_PAD_X

    def __init__(self, parent, text="IDLE", dot_color=None):
        self._text = text.upper()
        self._dot_color = dot_color or theme.INK_MUTED
        self._font = _resolve(theme.FONT_LIGHT_CHAIN, 11, "light")
        self._edge = _margin(theme.SHADOW_DEPTH_INNER, theme.SHADOW_BLUR_INNER)
        self._photo = None
        super().__init__(
            parent,
            width=self._surface_width() + self._edge * 2,
            height=self.HEIGHT + self._edge * 2,
            bg=theme.SURFACE,
            highlightthickness=0,
            bd=0,
        )
        self._render()

    def _surface_width(self):
        return (
            self.PAD_X * 2 + self.DOT_R * 2 + self.DOT_GAP
            + self._font.measure(self._text)
        )

    def set_state(self, text, dot_color):
        self._text = str(text).upper()
        self._dot_color = dot_color
        self.configure(width=self._surface_width() + self._edge * 2)
        self._render()

    def _render(self):
        self.delete("all")
        w = self._surface_width()
        h = self.HEIGHT
        self._photo = _blit(self, render.inset(w, h, theme.STATUS_BADGE_RADIUS))
        cy = self._edge + h / 2.0
        dot_cx = self._edge + self.PAD_X + self.DOT_R
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
    """Two-state switch: an inset track with a raised knob.

    The knob is an RGBA overlay. Rendering it opaque would bake the base
    colour across the whole shadow margin, and pasting that over the track
    painted a full-size rectangle on top of it.

    Its shadow uses the compact pair and the canvas is sized from whichever
    of track and knob needs more room. With the full pair the knob image
    came out taller than the track's canvas, so the falloff was cut at the
    canvas edge and the switch read as a hard-edged rectangle.
    """

    TRACK_W = theme.TOGGLE_TRACK_W
    TRACK_H = theme.TOGGLE_TRACK_H
    KNOB_D = theme.TOGGLE_KNOB_D
    KNOB_PAD = theme.TOGGLE_KNOB_PAD

    def __init__(self, parent, on_change=None):
        self._state = False
        self._focused = False
        self._hover = False
        self._on_change = on_change
        self._track_edge = _margin(theme.SHADOW_DEPTH_INNER, theme.SHADOW_BLUR_INNER)
        self._knob_edge = render.overlay_margin(
            render.COMPACT_DEPTH, render.COMPACT_BLUR
        )
        width = max(
            self.TRACK_W + self._track_edge * 2,
            self.KNOB_D + self._knob_edge * 2,
        )
        height = max(
            self.TRACK_H + self._track_edge * 2,
            self.KNOB_D + self._knob_edge * 2,
        )
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=theme.SURFACE,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
            takefocus=1,
        )
        self.bind("<Button-1>", self._toggle)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<FocusIn>", lambda _e: self.set_focused(True))
        self.bind("<FocusOut>", lambda _e: self.set_focused(False))
        self._track_photo = None
        self._knob_photo = None
        self._render()

    def _on_enter(self, _e):
        if self._hover:
            return
        self._hover = True
        self._render()

    def _on_leave(self, _e):
        self._hover = False
        self._render()

    def set_focused(self, focused):
        focused = bool(focused)
        if focused == self._focused:
            return
        self._focused = focused
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
        w, h = self.winfo_width(), self.winfo_height()
        e = self._track_edge
        cx = w / 2.0
        cy = h / 2.0
        ring = (theme.ACCENT, theme.FOCUS_RING_WIDTH) if self._focused else None
        base = theme.SURFACE_HOVER if self._hover else theme.SURFACE_SUNKEN
        track_w, track_h = self.TRACK_W, self.TRACK_H
        self._track_photo = _blit(
            self,
            render.inset(track_w, track_h, theme.TOGGLE_TRACK_R, base=base,
                         ring=ring),
            offset=(int(cx - track_w / 2.0), int(cy - track_h / 2.0)),
        )
        half = self.KNOB_D / 2.0
        if self._state:
            knob_cx = cx + track_w / 2.0 - half - self.KNOB_PAD
            knob_color = theme.ACCENT
        else:
            knob_cx = cx - track_w / 2.0 + half + self.KNOB_PAD
            knob_color = theme.SURFACE
        self._knob_photo = _blit(
            self,
            render.overlay(
                self.KNOB_D, knob_color,
                depth=render.COMPACT_DEPTH, blur=render.COMPACT_BLUR,
            ),
            offset=(
                render.overlay_offset(knob_cx, self.KNOB_D, self._knob_edge),
                render.overlay_offset(cy, self.KNOB_D, self._knob_edge),
            ),
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

    Rings, ticks, active arc, and needle are rasterised by Pillow; the tick
    labels and the readout stay as canvas text, which Xft already antialiases.

    Two things were wrong before and are worth keeping in mind:
    - PIL measures arc angles clockwise from 3 o'clock, so the top half of
      a ring is `start=180, end=360`. The opposite values draw the bottom
      half and the dial reads as loose tick marks with no rings at all.
    - Tick labels placed on a radius collide with the end tick marks and
      with the needle at the extremes. They are pinned just outside the
      outer ring at the three cardinal points instead, and the readout sits
      in the middle over a surface knockout so the needle passes behind it,
      the way it does in the reference.
    """

    # The readout is a three-line block: value, unit, then the pivot. The
    # needle has to clear it at 90 degrees, so the block sits high and the
    # needle stops short of the pivot centre.
    VALUE_OFFSET = -40
    SUB_OFFSET = -16
    VALUE_SIZE = 27
    SUB_SIZE = 9
    TICK_SIZE = 9
    LABEL_GAP = 8

    def __init__(self, parent, value=0, max_value=1000, label="CPS",
                 width=None, height=None):
        width = width or theme.GAUGE_WIDTH
        height = height or theme.GAUGE_HEIGHT
        self._gauge_w = width
        self._gauge_h = height
        self._cx = width / 2.0
        self._cy = height - render.DIAL_PIVOT_INSET
        self._value = 0
        self._target = 0
        self._max = max(1, max_value)
        self._label = label
        self._animation_after = None
        self._photo = None
        self._value_font = _resolve(theme.FONT_MONO_CHAIN, self.VALUE_SIZE, "light")
        self._sub_font = _resolve(theme.FONT_LIGHT_CHAIN, self.SUB_SIZE, "light")
        self._tick_font = _resolve(theme.FONT_LIGHT_CHAIN, self.TICK_SIZE, "light")
        super().__init__(
            parent, width=width, height=height,
            bg=theme.SURFACE, highlightthickness=0, bd=0,
        )
        self.set_value(value)

    def _sweep(self, value):
        """Map a value onto a dial angle, 180 (left) to 0 (right)."""
        fraction = 0.0 if self._max == 0 else value / float(self._max)
        fraction = max(0.0, min(1.0, fraction))
        return 180 - fraction * 180

    def set_value(self, value):
        self._target = max(0, min(float(value), self._max))
        if self._animation_after is None:
            self._animate()

    def _tick_label(self, index):
        """Pinned just outside the ring at the left, top, and right."""
        outer = render.DIAL_OUTER_R
        gap = self.LABEL_GAP
        # Tk anchors are compass pairs (e, w, center). PIL's r/l/m are not
        # valid here and raise at create_text time.
        if index == 0:
            return self._cx - outer - gap, self._cy + 1, "e"
        if index == theme.GAUGE_TICK_COUNT - 1:
            return self._cx + outer + gap, self._cy + 1, "w"
        return self._cx, self._cy - outer - gap, "center"

    def _paint(self):
        self.delete("all")
        self._photo = _blit(
            self, render.dial(self._gauge_w, self._gauge_h, self._sweep, self._value)
        )

        for i in (0, (theme.GAUGE_TICK_COUNT - 1) // 2, theme.GAUGE_TICK_COUNT - 1):
            x, y, anchor = self._tick_label(i)
            self.create_text(
                x, y,
                text=str(int(round(i / float(theme.GAUGE_TICK_COUNT - 1) * self._max))),
                font=self._tick_font, fill=theme.INK_MUTED, anchor=anchor,
            )

        # The readout sits over a surface knockout: the needle is drawn under
        # it, and clipping the number out of the needle is what the reference
        # does rather than shortening the needle out of the dial.
        text = f"{int(round(self._value))}"
        value_y = self._cy + self.VALUE_OFFSET
        sub_y = self._cy + self.SUB_OFFSET
        half_w = max(
            self._value_font.measure(text) / 2.0,
            self._sub_font.measure(self._label.upper()) / 2.0,
        ) + 9
        self.create_rectangle(
            self._cx - half_w, value_y - self.VALUE_SIZE * 0.7,
            self._cx + half_w, sub_y + self.SUB_SIZE,
            fill=theme.SURFACE, outline="",
        )
        self.create_text(
            self._cx, value_y, text=text,
            font=self._value_font, fill=theme.INK_STRONG, anchor="center",
        )
        self.create_text(
            self._cx, sub_y, text=self._label.upper(),
            font=self._sub_font, fill=theme.INK_MUTED, anchor="center",
        )

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
        self._photo = None
        self._edge = _margin()
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
            pad = self._edge + 12
            canvas.configure(
                width=body.winfo_reqwidth() + pad * 2,
                height=body.winfo_reqheight() + pad * 2,
            )
            canvas.coords(body_window, pad, pad)
            self._draw_shadow(canvas, border=border)
            # The blit is appended last, so lift the text back above it.
            canvas.tag_raise(body_window)

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
        surface_w = w - self._edge * 2
        surface_h = h - self._edge * 2
        if surface_w <= 0 or surface_h <= 0:
            return
        # The error border is part of the rasterised surface. A canvas
        # rectangle drew it square, with corners that missed the popover's
        # SMALL_RADIUS arc.
        ring = (border, theme.FOCUS_RING_WIDTH) if border else None
        # Keep a live reference: Tk does not own the image buffer, so
        # dropping it blanks the canvas.
        self._photo = _blit(
            canvas,
            render.raised(
                surface_w, surface_h, theme.SMALL_RADIUS, ring=ring,
            ),
        )

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
