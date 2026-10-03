"""Antialiased shape rendering for the Neumorphic surfaces.

Tk draws Canvas items through the X11 core protocol, which has no
antialiasing: a rounded edge is a hard step from surface to fill, and no Tk
option changes that. Text is the exception, because that path goes through
Xft and is already antialiased.

So shapes are rasterised here with Pillow: draw at SUPERSAMPLE times the
target size, then downscale with LANCZOS. That produces the multi-pixel grey
ramp along a curved edge instead of a staircase.

Every result is cached. A pill button repaints on each hover change, and
re-rasterising a 104x50 pill at 4x on every repaint would cost more than the
repaint it is fixing.
"""

import math

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageTk

from autoclicker.ui import theme

SUPERSAMPLE = 4
_CACHE_LIMIT = 512

# Dial geometry, in target pixels. The pivot sits 16px off the bottom edge.
DIAL_OUTER_R = 64
DIAL_INNER_R = 44
DIAL_NEEDLE_REACH = 40
DIAL_PIVOT_INSET = 16


def _hex(value):
    """Accept '#RRGGBB' or an (r, g, b) tuple and return an (r, g, b) tuple."""
    if isinstance(value, (tuple, list)):
        return tuple(int(c) for c in value)
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def _blend(a, b, t):
    ra, ga, ba = _hex(a)
    rb, gb, bb = _hex(b)
    return (
        int(ra + (rb - ra) * t),
        int(ga + (gb - ga) * t),
        int(ba + (bb - ba) * t),
    )


def _shadow_pair(base_hex):
    """Highlight and shadow colours derived from the surface they sit on.

    Fixed shadow colours only work on a light base. On the accent fill the
    shadow colour was lighter than the fill itself, so the dark shadow
    measured -1 against a base of 123 while the white highlight measured +116:
    a solid slab with a glow, not a raised surface. Deriving both from the
    base keeps the pair symmetric on any fill.
    """
    base = _hex(base_hex)
    highlight = tuple(int(c + (255 - c) * 0.78) for c in base)
    shadow = tuple(int(c * 0.74) for c in base)
    return highlight, shadow


class _Cache:
    """Bounded memo keyed on every input that changes the pixels."""

    def __init__(self, limit=_CACHE_LIMIT):
        self._store = {}
        self._limit = limit

    def get(self, key, build):
        hit = self._store.get(key)
        if hit is not None:
            return hit
        value = build()
        if len(self._store) >= self._limit:
            self._store.clear()
        self._store[key] = value
        return value

    def clear(self):
        self._store.clear()


_cache = _Cache()


def _paint(surface_w, surface_h, radius, depth, blur, base, invert=False,
           ring=None):
    """One raised or inset surface, drawn at SUPERSAMPLE then downscaled.

    The shadow is a real Gaussian blur of the shape's own silhouette,
    offset in each direction, not a stack of concentric outlines. The stack
    was wrong twice over: it produced a stepped falloff rather than a smooth
    one, and its outermost ring fell outside the image and was clipped, so
    the shadow looked cut off at the card edge.

    `depth` is the shadow offset and `blur` its sigma. The margin is derived
    from both so the full falloff always fits inside the image.

    The margin is transparent. A filled margin meant the base colour was
    painted across the whole image, so a control whose fill was not the
    window colour (a hovered button, an inset well) showed the canvas-sized
    rectangle its shadow sat in instead of just its silhouette.
    """
    s = SUPERSAMPLE
    margin = depth + math.ceil(3 * blur)
    full_w = (surface_w + margin * 2) * s
    full_h = (surface_h + margin * 2) * s
    image = Image.new("RGB", (full_w, full_h), _hex(base))

    box = [
        margin * s, margin * s,
        (margin + surface_w) * s - 1, (margin + surface_h) * s - 1,
    ]
    radius_px = max(int(radius * s), 0)

    silhouette = Image.new("L", (full_w, full_h), 0)
    ImageDraw.Draw(silhouette).rounded_rectangle(box, radius=radius_px, fill=255)
    coverage = silhouette.copy()

    # The two shadows are separate light contributions, so they are composed
    # additively into one layer. Pasting them straight onto the base let the
    # dark one overwrite the light one, which is why the highlight measured +7
    # against a base of 224 while the shadow measured -37: the neumorphic lift
    # was one-sided and the cards read as flat on the top and left.
    highlight, shadow = _shadow_pair(base)
    # An inset well is lit from the opposite side: dark up-left, light
    # down-right. `invert` swaps which pair goes where.
    first, second = (shadow, highlight) if invert else (highlight, shadow)
    layer = Image.new("RGBA", (full_w, full_h), (0, 0, 0, 0))
    for shift, color in ((-depth * s, first), (depth * s, second)):
        mask = Image.new("L", (full_w, full_h), 0)
        mask.paste(silhouette, (shift, shift))
        mask = mask.filter(ImageFilter.GaussianBlur(blur * s))
        coverage = ImageChops.lighter(coverage, mask)
        contribution = Image.new("RGBA", (full_w, full_h), _hex(color) + (0,))
        contribution.putalpha(mask)
        layer = Image.alpha_composite(layer, contribution)
    image = Image.alpha_composite(image.convert("RGBA"), layer).convert("RGB")

    # The surface itself, crisp, on top of its own shadow.
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(box, radius=radius_px, fill=_hex(base))

    # A focus ring is a curve, so it has to be rasterised too. Baked in here
    # rather than drawn as a canvas overlay, which would be a staircase.
    if ring:
        ring_color, ring_width = ring
        grow = int(theme.FOCUS_RING_OFFSET * s) + int(ring_width * s)
        ring_box = [
            box[0] - grow, box[1] - grow, box[2] + grow, box[3] + grow,
        ]
        draw.rounded_rectangle(
            ring_box,
            radius=radius_px + grow,
            outline=_hex(ring_color),
            width=max(int(ring_width * s), 1),
        )
        # The ring sits out in the margin, where the shadow has already faded,
        # so it has to claim its own opacity or it washes out.
        ImageDraw.Draw(coverage).rounded_rectangle(
            ring_box, radius=radius_px + grow,
            outline=255, width=max(int(ring_width * s), 1),
        )

    image = image.convert("RGBA")
    image.putalpha(coverage)
    return image.resize(
        (surface_w + margin * 2, surface_h + margin * 2),
        Image.Resampling.LANCZOS,
    )


# Compact shadow for small controls. A 26px help button carrying the full
# 13px margin became 52px of canvas, which is what pushed the settings
# fields past the height the column could give them.
COMPACT_DEPTH = 3
COMPACT_BLUR = 1.5


def margin_for(depth, blur):
    """Pixels the shadow needs on each side. Callers size their canvas by it.

    A Gaussian of sigma `blur` offset by `depth` needs `depth + ceil(3*blur)`
    to hold its whole falloff. Reserving only `depth + 2*blur` cut the last
    sigma off at the image edge, which showed as a hard straight line exactly
    where the falloff stopped.
    """
    return depth + math.ceil(3 * blur)


def raised(width, height, radius, base=None, lift=0, depth=None, blur=None,
           ring=None):
    """Outset surface: light shadow up-left, dark shadow down-right.

    The returned image is RGBA with a transparent margin, so a fill other
    than the canvas colour changes only the silhouette, never the box.
    """
    depth = (theme.SHADOW_DEPTH if depth is None else depth) + lift
    blur = theme.SHADOW_BLUR if blur is None else blur
    base = theme.SURFACE if base is None else base
    return _cache.get(
        ("raised", width, height, radius, depth, blur, base, ring),
        lambda: _paint(
            width, height, radius, depth, blur, base, ring=ring,
        ),
    )


def inset(width, height, radius, base=None, depth=None, blur=None, ring=None):
    """Inset well: dark shadow up-left, light shadow down-right.

    Same transparent margin as `raised`: an inset well that filled its own
    margin painted a sunken rectangle around itself on the card.
    """
    depth = theme.SHADOW_DEPTH_INNER if depth is None else depth
    blur = theme.SHADOW_BLUR_INNER if blur is None else blur
    base = theme.SURFACE_SUNKEN if base is None else base
    return _cache.get(
        ("inset", width, height, radius, depth, blur, base, ring),
        lambda: _paint(
            width, height, radius, depth, blur, base, invert=True, ring=ring,
        ),
    )


def circle(size, base=None, well=True, depth=None, blur=None):
    """A round well or knob: the same recipe with a full-box radius."""
    base = theme.SURFACE if base is None else base
    if well:
        return raised(size, size, size // 2, base=base, depth=depth, blur=blur)
    return inset(size, size, size // 2, base=base, depth=depth, blur=blur)



def dial(width, height, angle_for, value, scale=1.0, sweep_key=None):
    """Rings, ticks, active arc, and needle for the CPS dial, as one image.

    Repainted on every animation frame, so it is cached on the painted
    value. The ease-out settles in roughly 25 distinct steps, which turns
    into about 25 cached renders rather than one per frame.

    `sweep_key` names the scale the angles were drawn against. The dial
    rescales per run, so a cache keyed on the value alone served the
    previous run's arc and needle to the next one.
    """
    return _cache.get(
        ("dial", width, height, round(value, 1), scale, sweep_key),
        lambda: _dial(width, height, angle_for, value, scale),
    )


def _polar(cx, cy, angle_deg, radius):
    import math
    rad = math.radians(angle_deg)
    return cx + radius * math.cos(rad), cy - radius * math.sin(rad)


def _dial(width, height, angle_for, value, scale):
    """Rings, ticks, active arc, and needle for the CPS dial.

    The pivot sits near the bottom edge and the rings are sized to leave
    headroom, so the arc is a clean half-dial instead of a squashed one.
    Tick labels go inside the ring band: outside, the 0 and 1000 labels ran
    into the canvas edge and collided with the end tick marks.
    """
    s = SUPERSAMPLE
    big = Image.new("RGB", (width * s, height * s), _hex(theme.SURFACE))
    draw = ImageDraw.Draw(big)
    cx = width / 2.0 * s
    cy = (height - 16) * s
    outer = DIAL_OUTER_R * scale * s
    inner = DIAL_INNER_R * scale * s
    label_r = (outer + inner) / 2.0

    # PIL measures arc angles clockwise from 3 o'clock, so the top half is
    # 180 -> 360. Passing 0 -> 180 drew the bottom half and left the dial
    # reading as a scatter of tick marks with no rings at all.
    for radius in (outer, inner):
        draw.arc(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            start=180, end=360, fill=_hex(theme.INK_FAINT), width=max(s, 1),
        )

    count = theme.GAUGE_TICK_COUNT
    for i in range(count):
        angle = 180 - (i / float(count - 1)) * 180
        major = i in (0, (count - 1) // 2, count - 1)
        x1, y1 = _polar(cx, cy, angle, outer)
        x2, y2 = _polar(cx, cy, angle, outer - (11 if major else 5) * scale * s)
        draw.line(
            [x1, y1, x2, y2],
            fill=_hex(theme.INK if major else theme.INK_FAINT),
            width=max(int((1.6 if major else 1.0) * s), 1),
        )

    if value > 0:
        draw.arc(
            [cx - inner, cy - inner, cx + inner, cy + inner],
            start=180, end=180 + max(180 - angle_for(value), 0.01),
            fill=_hex(theme.ACCENT), width=max(int(2 * s), 1),
        )

    nx, ny = _polar(cx, cy, angle_for(value), DIAL_NEEDLE_REACH * scale * s)
    draw.line([cx, cy, nx, ny], fill=_hex(theme.ACCENT), width=max(int(2.4 * s), 1))
    tip = 3.5 * scale * s
    draw.ellipse([nx - tip, ny - tip, nx + tip, ny + tip], fill=_hex(theme.ACCENT))
    pivot = 5 * scale * s
    draw.ellipse(
        [cx - pivot, cy - pivot, cx + pivot, cy + pivot],
        fill=_hex(theme.ACCENT), outline=_hex(theme.SURFACE),
        width=max(int(2 * s), 1),
    )
    return big.resize((width, height), Image.Resampling.LANCZOS)


def overlay_offset(canvas_centre, size, margin):
    """Canvas coordinate for an overlay image.

    An overlay image is `size + 2*margin` wide and its disc occupies the
    middle `size`, so the disc centre sits at `margin + size/2` inside the
    image. To land that centre on a canvas coordinate, blit at
    `canvas_centre - (margin + size/2)`. Blitting at the margin alone leaves
    the disc offset by its own radius.
    """
    return int(round(canvas_centre - (margin + size / 2.0)))


def to_photo(master, image, **kwargs):
    """Wrap a Pillow image as a Tk image.

    The caller must keep a reference: Tk does not own the underlying
    buffer, so dropping the PhotoImage blanks the widget.
    """
    return ImageTk.PhotoImage(image, master=master, **kwargs)


def overlay(size, color, radius=None, depth=None, blur=None, base=None,
            invert=False):
    """An RGBA piece that composites over whatever is already painted.

    An `overlay` is a shape that composites over another surface rather than
    replacing one: the toggle knob sits on the track, and an opaque piece
    would paste a full-size rectangle over it. Returns transparency
    everywhere except the silhouette and its shadow.
    """
    depth = theme.SHADOW_DEPTH if depth is None else depth
    blur = theme.SHADOW_BLUR if blur is None else blur
    radius = size // 2 if radius is None else radius
    base = color if base is None else base
    return _cache.get(
        ("overlay", size, color, radius, depth, blur, base, invert),
        lambda: _overlay(size, color, radius, depth, blur, base, invert),
    )


def _overlay(size, color, radius, depth, blur, base, invert):
    s = SUPERSAMPLE
    margin = depth + math.ceil(3 * blur)
    full = (size + margin * 2) * s
    image = Image.new("RGBA", (full, full), (0, 0, 0, 0))
    m = margin * s
    box = [m, m, m + size * s - 1, m + size * s - 1]
    radius_px = max(int(radius * s), 0)

    silhouette = Image.new("L", (full, full), 0)
    ImageDraw.Draw(silhouette).rounded_rectangle(box, radius=radius_px, fill=255)

    highlight, shade = _shadow_pair(base)
    first, second = (shade, highlight) if invert else (highlight, shade)
    for shift, shadow_color in ((-depth * s, first), (depth * s, second)):
        mask = Image.new("L", (full, full), 0)
        mask.paste(silhouette, (shift, shift))
        mask = mask.filter(ImageFilter.GaussianBlur(blur * s))
        contribution = Image.new("RGBA", (full, full), _hex(shadow_color) + (0,))
        contribution.putalpha(mask)
        image = Image.alpha_composite(image, contribution)

    disc = Image.new("RGBA", (full, full), (0, 0, 0, 0))
    ImageDraw.Draw(disc).rounded_rectangle(box, radius=radius_px, fill=_hex(color) + (255,))
    image = Image.alpha_composite(image, disc)
    return image.resize(
        (size + margin * 2, size + margin * 2), Image.Resampling.LANCZOS
    )


def overlay_margin(depth=None, blur=None):
    """Transparent padding around an `overlay` piece."""
    depth = theme.SHADOW_DEPTH if depth is None else depth
    blur = theme.SHADOW_BLUR if blur is None else blur
    return margin_for(depth, blur)
