"""Neumorphism design tokens shared by every UI module.

Single source of truth for palette, geometry, and typography. Every other UI
module reads from here, so a palette change happens in one place.
"""

# ---- palette ----
# One surface color for the window and for every raised element. Depth comes
# only from the shadow pair, never from a second fill.

SURFACE = "#E0E5EC"
SURFACE_SUNKEN = "#D6DCE4"   # inset wells: entries, toggle track, status pill
SURFACE_HOVER = "#E8EDF3"    # button hover

SHADOW_DARK_HEX = "#A3B1C6"  # bottom-right shadow
SHADOW_LIGHT_HEX = "#FFFFFF" # top-left highlight

INK_STRONG = "#3D4654"  # values, card titles
INK = "#5A6473"        # body copy, tooltips
INK_MUTED = "#8993A4"   # field labels, metadata
INK_FAINT = "#B6BDC9"   # tick marks, disabled text

ACCENT = "#7B8AA1"       # needle, focus ring, primary fill
ACCENT_SOFT = "#A6B0C2"  # text selection

DANGER = "#C0566B"   # invalid field, error state
SUCCESS = "#5C9A7B"  # running state
PAUSED = "#D69E2E"   # countdown, warning state

# ---- geometry ----

WINDOW_SIZE = "560x480"
WINDOW_MIN_SIZE = (560, 480)

CARD_PADDING = 20
CARD_PADDING_TIGHT = 16
CARD_RADIUS = 26
SMALL_RADIUS = 12  # tooltip corners

SPACE_3 = 12
SPACE_4 = 16

SHADOW_OFFSET = 5
SHADOW_BLUR_STEPS = 10
SHADOW_OFFSET_INNER = 3
SHADOW_BLUR_STEPS_INNER = 6

FOCUS_RING_WIDTH = 2
FOCUS_RING_OFFSET = 2

# ---- typography ----
# Tk only accepts "normal" and "bold" as weights, so a "light" face is
# approximated by asking for normal at one point smaller. resolve_font picks
# the first family the running system actually has.

FONT_LIGHT_CHAIN = (
    "Helvetica Neue Light",
    "Segoe UI Light",
    "Inter Light",
    "Arial",
    "sans-serif",
)
FONT_REGULAR_CHAIN = (
    "Helvetica Neue",
    "Segoe UI",
    "Inter",
    "Arial",
    "sans-serif",
)
FONT_MONO_CHAIN = (
    "SF Mono Light",
    "Consolas",
    "Menlo",
    "Courier New",
    "monospace",
)

FONT_INPUT = (FONT_REGULAR_CHAIN, 13, "normal")
FONT_BUTTON = (FONT_LIGHT_CHAIN, 12, "light")

# ---- icons ----

ICON_BOX = 28      # catalog glyphs are authored in this square
ICON_STROKE = 1.6
ICON_COLOR = INK
ICON_COLOR_ACTIVE = INK_STRONG
ICON_COLOR_DISABLED = INK_FAINT
ICON_COLOR_ACCENT = ACCENT

# ---- dial ----

GAUGE_WIDTH = 200
GAUGE_HEIGHT = 108
GAUGE_OUTER_R = 76
GAUGE_INNER_R = 56
GAUGE_TICK_COUNT = 11


def hex_to_rgb(value):
    """Convert '#RRGGBB' to (r, g, b) ints."""
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    """Convert (r, g, b) ints back to '#RRGGBB'."""
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def blend(color_a, color_b, t):
    """Linear interpolate two hex colors. t in [0, 1]."""
    ra, ga, ba = hex_to_rgb(color_a)
    rb, gb, bb = hex_to_rgb(color_b)
    return rgb_to_hex(
        (
            int(ra + (rb - ra) * t),
            int(ga + (gb - ga) * t),
            int(ba + (bb - ba) * t),
        )
    )


def font_to_tk(font_tuple):
    """Convert a token font tuple into a spec Tk will accept."""
    if not isinstance(font_tuple, tuple) or len(font_tuple) != 3:
        return font_tuple
    chain, size, weight = font_tuple
    family = chain if isinstance(chain, str) else (chain[0] if chain else "Arial")
    return (
        family,
        size - 1 if weight == "light" else size,
        "normal" if weight in ("light", "normal") else "bold",
    )


def resolve_font(chain, size, weight):
    """Return a real tkfont.Font for the first family in `chain` that exists.

    "light" is not a Tk weight, so it resolves to normal at one point
    smaller, which reads lighter on every platform.
    """
    import tkinter.font as tkfont

    tk_weight = "normal" if weight in ("light", "normal") else "bold"
    effective_size = size - 1 if weight == "light" else size
    for family in chain:
        try:
            font = tkfont.Font(family=family, size=effective_size, weight=tk_weight)
            font.measure("A")
            return font
        except Exception:
            continue
    try:
        return tkfont.Font(family="Arial", size=effective_size, weight=tk_weight)
    except Exception:
        return tkfont.Font(family="TkDefaultFont", size=effective_size, weight=tk_weight)
