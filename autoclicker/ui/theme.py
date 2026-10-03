"""Neumorphism design tokens shared by every UI module.

Single source of truth for palette, geometry, typography. Importing modules
must read from here so palette changes happen in one place.
"""

SURFACE = "#E0E5EC"
SURFACE_SUNKEN = "#D6DCE4"
SURFACE_HOVER = "#E8EDF3"

SHADOW_DARK_RGB = (163, 177, 198)
SHADOW_LIGHT_RGB = (255, 255, 255)
SHADOW_DARK_PRESSED_RGB = (176, 188, 207)
SHADOW_LIGHT_PRESSED_RGB = (245, 248, 253)

SHADOW_DARK_HEX = "#A3B1C6"
SHADOW_LIGHT_HEX = "#FFFFFF"

INK_STRONG = "#3D4654"
INK = "#5A6473"
INK_MUTED = "#8993A4"
INK_FAINT = "#B6BDC9"

ACCENT = "#7B8AA1"
ACCENT_SOFT = "#A6B0C2"

DANGER = "#C0566B"
SUCCESS = "#5C9A7B"
PAUSED = "#D69E2E"

DIVIDER = "#C9D2DE"

WINDOW_SIZE = "560x480"
WINDOW_MIN_SIZE = (560, 480)
WINDOW_BG = SURFACE

CARD_PADDING = 20
CARD_PADDING_TIGHT = 16
CARD_RADIUS = 26
SCENE_RADIUS = 22
LIST_RADIUS = 18
PILL_RADIUS = 999
SMALL_RADIUS = 12

SPACE_1 = 4
SPACE_2 = 8
SPACE_3 = 12
SPACE_4 = 16
SPACE_5 = 24
SPACE_6 = 32
SPACE_7 = 40

SHADOW_OFFSET = 5
SHADOW_BLUR_STEPS = 10
SHADOW_ALPHA_PEAK_DARK = 0.55
SHADOW_ALPHA_PEAK_LIGHT = 0.85

SHADOW_OFFSET_INNER = 3
SHADOW_BLUR_STEPS_INNER = 6
SHADOW_ALPHA_PEAK_INNER = 0.35

FOCUS_RING_WIDTH = 2
FOCUS_RING_OFFSET = 2

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

# Resolved font objects. These are created lazily on first access because
# Tkinter requires a Tk root to resolve some font queries. We expose
# helpers instead of pre-built tuples.
def font(chain, size, weight):
    """Return a tkfont.Font-like object. Resolved lazily."""
    return (chain, size, weight)


FONT_DISPLAY = font(FONT_LIGHT_CHAIN, 32, "light")
FONT_CARD_TITLE = font(FONT_LIGHT_CHAIN, 12, "light")
FONT_SECTION = font(FONT_LIGHT_CHAIN, 10, "light")
FONT_FIELD_LABEL = font(FONT_LIGHT_CHAIN, 11, "light")
FONT_INPUT = font(FONT_REGULAR_CHAIN, 13, "normal")
FONT_BUTTON = font(FONT_LIGHT_CHAIN, 12, "light")
FONT_HELP = font(FONT_LIGHT_CHAIN, 13, "light")
FONT_BODY = font(FONT_REGULAR_CHAIN, 13, "normal")
FONT_SUB = font(FONT_LIGHT_CHAIN, 10, "light")
FONT_GAUGE_VALUE = font(FONT_MONO_CHAIN, 22, "light")
FONT_GAUGE_SUB = font(FONT_LIGHT_CHAIN, 9, "light")
FONT_GAUGE_TICK = font(FONT_LIGHT_CHAIN, 9, "light")
FONT_STATUS = font(FONT_LIGHT_CHAIN, 11, "light")
FONT_RUN_LARGE = font(FONT_LIGHT_CHAIN, 16, "light")
FONT_TOOLTIP = font(FONT_REGULAR_CHAIN, 12, "normal")


def font_to_tk(font_tuple):
    """Convert a theme font tuple to a tk-compatible spec.

    Tk only accepts string family names plus size and weight. We resolve
    the chain here so callers can pass the resulting tuple to any widget.
    """
    if not isinstance(font_tuple, tuple) or len(font_tuple) != 3:
        return font_tuple
    chain, size, weight = font_tuple
    if isinstance(chain, str):
        return (chain, size, "normal" if weight in ("light", "normal") else "bold")
    # chain is a list of family fallbacks; pick the first one and return
    # a single tuple.
    family = chain[0] if chain else "Arial"
    return (family, size - 1 if weight == "light" else size,
            "normal" if weight in ("light", "normal") else "bold")

ICON_BOX = 28
ICON_WELL = 36
ICON_STROKE = 1.6
ICON_COLOR = INK
ICON_COLOR_ACTIVE = INK_STRONG
ICON_COLOR_DISABLED = INK_FAINT
ICON_COLOR_ACCENT = ACCENT

GAUGE_WIDTH = 200
GAUGE_HEIGHT = 108
GAUGE_OUTER_R = 76
GAUGE_INNER_R = 56
GAUGE_NEEDLE_LEN = 48
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


def blend_rgb(rgb_a, rgb_b, t):
    return tuple(
        int(a + (b - a) * t)
        for a, b in zip(rgb_a, rgb_b)
    )


def resolve_font(chain, size, weight):
    """Pick the first family in `chain` that Tk can resolve.

    On systems without the named face, returns a fallback that approximates
    a lighter weight by reducing the size by 1px.
    """
    import tkinter.font as tkfont
    tk_weight = "normal" if weight in ("light", "normal") else "bold"
    effective_size = size - 1 if weight == "light" else size
    for family in chain:
        try:
            f = tkfont.Font(family=family, size=effective_size, weight=tk_weight)
            f.measure("A")
            return f
        except Exception:
            continue
    try:
        return tkfont.Font(family="Arial", size=effective_size, weight=tk_weight)
    except Exception:
        return tkfont.Font(family="TkDefaultFont", size=effective_size, weight=tk_weight)


def lighten(color, amount):
    return blend(color, SHADOW_LIGHT_HEX, amount)


def darken(color, amount):
    return blend(color, SHADOW_DARK_HEX, amount)
