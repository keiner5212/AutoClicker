# Changelog

## 2.5 - The shadows were one-sided and the cards had none at all

### The card shadow was covered
`NeumoCard` packed its content Frame with `fill="both", expand=True`, edge to
edge, with `bg=SURFACE`. That flat background covered the entire card,
including the shadow ring the Canvas underneath was rendering. The cards were
never showing a shadow; they were rectangles of flat base colour with a
hairline where the image ended. The content frame is now inset by the shadow
margin, so the ring is visible.

### The highlight was being cancelled by the shadow
Measured on a card against a base of 224: the dark shadow reached -37 and the
light highlight only +7. The cause was `depth=3` with `blur=5`. The dark
shadow is the silhouette offset down-right, and with a 5px sigma its falloff
reached 10px back across the surface, landing on top of the light shadow's
own band and subtracting most of it. The lift was one-sided, so the cards
read as flat on the top and left.

Measured across parameter sets rather than guessed:

| depth | blur | highlight | shadow | ratio |
|---|---|---|---|---|
| 3 | 5 | +7 | -36 | 5.1 (rejected) |
| 4 | 4 | +15 | -45 | 3.0 |
| 5 | 3 | +26 | -42 | 1.6 (chosen) |

Now `SHADOW_DEPTH=5`, `SHADOW_BLUR=3`. Card and button measure +20 / -53,
compact controls +19 / -49, inset wells -43 / +26.

### Shadows now derive from the surface they sit on
Fixed shadow colours only work on a light base. On the accent fill the dark
shadow colour was lighter than the fill itself, so it measured -1 against a
base of 123 while the white highlight measured +116: a flat slab with a glow.
The renderer now derives both from the base colour, so the pair stays
symmetric on any fill. The primary button also became a surface pill with
accent text, which is what the reference does; a solid accent slab is the one
thing that cannot read as neumorphic.

### Shadows composite additively
The highlight and the shadow are separate light contributions, so they are
composed into one RGBA layer rather than pasted one over the other onto the
base.

### Size
Cards grew 22px once the content frame stopped covering the shadow margin.
The window is now 560x540. All four cards verified to contain their content,
and the action bar verified inside the window bounds.

Build stamp is now `v2.5 build 05376d9a`.

## 2.4 - The surfaces were blitted at the wrong offset

### What was actually wrong
A rendered surface already contains the margin its shadow needs, so it fills
its Canvas exactly. Every widget was blitting it at `(edge, edge)` anyway,
adding the margin a second time. The consequence on every card, button,
input, badge, and tooltip:

- the surface shifted right and down by the full margin,
- the left and top highlight was cut off entirely, which is why the cards
  looked flat with no lift,
- the right and bottom shadow was clipped by the Canvas edge,
- what was left on the right was a band of bare base colour.

The toggle knob had the same class of error twice over: it was offset by its
own margin instead of by `margin + radius`, so the disc sat one radius right
of the track.

### Fix
`_blit` now always paints at the Canvas origin. The only non-zero offset is
an explicit `offset=` for an overlay, positioned with
`render.overlay_offset`, which takes the radius into account.

Verified numerically: the rendered image is now the same size as the Canvas
it lands on, for cards, buttons, and inputs. Every widget in every card is
inside its card's content area. 20/20 functional checks pass.

### On the preview
The composite preview I used to inspect layout pasted at the same wrong
offset, so it reproduced the bug instead of catching it. That is why the
captures looked fine and the app did not. The preview now blits at the
widget's absolute position, the way the widget does.

The X display in this environment is virtual and screenshots of it come back
blank, which is why the preview exists at all. It is a layout and surface
proxy, not a screenshot: text metrics come from DejaVu rather than the
theme's font chain, so font rendering and live hover are not represented.

## 2.3 - Layout and compositing fixes

### The real cause of the broken shapes
`render.raised` bakes the base colour into the whole image, including the
shadow margin. That is correct for a card, and wrong for anything drawn on
top of another surface: the toggle knob pasted an opaque rectangle over its
own track. Added `render.overlay`, which returns RGBA so a piece composites
over whatever is already there.

### Dial
- PIL measures arc angles clockwise from 3 o'clock, the opposite sense to
  Tk. The top half of a ring is `180 -> 360`; the values in use drew the
  bottom half, so the dial rendered as loose tick marks with no rings.
- Tick anchors were PIL's `r` / `l` / `m`. Tk wants compass pairs (`e`,
  `w`, `center`) and raised at paint time.
- Tick labels were on a radius that collided with the end tick marks and
  with the needle at the extremes. Pinned just outside the ring at the three
  cardinal points, with the readout raised so the needle clears it.
- Dial is 220x126 instead of 200x108, and the readout is a value + unit
  block rather than a number sitting on the pivot.

### Layout
- Settings fields stack the label above the input. Side by side in a 256px
  column, the label and help button consumed 150 of the 200px of usable
  width and left the input about 40px.
- The help button gets a compact shadow. A 26px button carrying the full
  13px margin occupied 52px of canvas, and three of those ran the settings
  card 20px past the available height.
- The action bar was clipped: it needed 88px and the column gave it 78.
- The status pill and the always-on-top switch now share a row.
- Both columns are 258px and balance to within 5px, so the action bar sits
  on a common baseline instead of leaving a gap under one column.

### Verification
Added a preview path that composites a PNG from the running app's real
geometry and the same render calls the widgets make. The X display here is
virtual and screenshots come back black, so this is how the layout was
actually inspected. All four cards verified to contain their content with no
clipping. 28/28 functional checks pass.

## 2.2 - Antialiased rendering

### Why
Tk draws Canvas items through the X11 core protocol, which has no
antialiasing. There is no option to enable it: a rounded edge is a hard step
from surface to fill. Text is the exception, because that path goes through
Xft and was already smooth. So the jaggedness was every shape and nothing
else.

### What
- `ui/render.py` rasterises every surface with Pillow: draw at 4x, then
  LANCZOS down to size. Pillow was the Designer's recommended path in the
  original spec and the first pass rejected it for a canvas-stack
  approximation. That approximation is what cost the smoothness.
- Shadows are now a real Gaussian blur of the shape's silhouette, offset per
  direction. The old 10-ring stack gave a stepped falloff, and its outermost
  ring fell outside the image and was clipped, so shadows looked cut off at
  the card edge.
- Converted: cards, pill buttons, status badge, toggle track and knob, input
  wells, icon wells, tooltips, and the dial.
- Focus rings baked into the rendered image. A ring is a curve, so a canvas
  overlay would have been a staircase again.
- Text, tick labels, and the value readout stay as canvas items, which Xft
  already antialiases.
- All renders are cached. A button repaints on every hover change; cached
  lookups are free, a cold render is 6.7 ms, and the full dial animation is
  78 ms for its 25 frames.

### Measured
Edge scanline across a button pill, surface `#E0E5EC` to fill `#FFFFFF`:
before `224, 224, 224, 255, 255` (one-pixel step). After `224, 224, 225,
225, 226, 226, 227, 228, 229, 230, 230, 231, 232, 233`. Shadow falloff now
passes through 9 distinct levels over 16px instead of jumping.

### Dependency
- Pillow added to `requirements.txt` and installed in the project venv. No
  global packages.

### Fix
- `NeumoGauge` stored its size in `self._w` / `self._h`, which collide with
  `tkinter.Misc._w`, the widget's Tk path name. `super().__init__()`
  overwrote them with a string, so the dial renderer got a string where an
  int belonged. Renamed to `_gauge_w` / `_gauge_h`.

## 2.1 - Compact UI, controls rebuilt

### Removed
- Macro feature. `MacroEngine`, `MacroRecorder`, the step list, the Run/Stop
  macro control, and the macro JSON file are all deleted. It was too much to
  land at once alongside the new UI, and the engine was mostly untested
  surface. The compact layout leaves room to re-add it as one more card.

### UI
- Window is 560x480: dial and status on the left, settings on the right, and
  a full-width action bar underneath. Cards hug their content height instead
  of stretching into empty slabs.
- Every control now paints itself on a single Canvas. Buttons that hosted a
  child Frame for their label had a rectangular background painted over the
  rounded pill, and the focus ring drew as a hard box.
- Pills are composed from two caps and a body instead of a smoothed polygon.
  A smoothing polygon whose radius reaches half the height collapses back
  into a rectangle, which is what the Start/Stop/Quit pills were doing.
- Inputs use `tk.Entry` instead of `ttk.Entry`. ttk paints a themed border
  that `borderwidth=0` does not remove, so every field had a hard outline.
- The status badge draws its dot and its label on the same Canvas. It was a
  Canvas plus a Label side by side, so the inset pill wrapped only the dot and
  the text sat on the bare surface as a separate box.
- Dial angle convention fixed. Tk measures 0 degrees at 3 o'clock counting
  counterclockwise, so a top half-dial is `start=0, extent=180`; the previous
  values drew the bottom half while the ticks swept the top.
- Dial tick labels moved inside the canvas bounds, and the value now draws
  last over a surface knockout so the needle passes behind the number.
- Dial reads the real 0-1000 CPS range and labels the ticks 0 / 500 / 1000.

### Behaviour
- All three fields validate on every Start, so a bad pause key no longer
  hides a bad countdown. Each field gets its own ring; the badge names the
  first problem.
- Worker threads no longer touch widgets or call `after` directly. The
  clicker and the hotkey listener push callables onto a queue that the main
  loop drains, which removes the "main thread is not in main loop" crash on
  exit.
- The click loop resyncs when it falls behind instead of drifting, and sleeps
  in slices so Stop stays responsive at high CPS.
- Settings and the always-on-top preference persist to `settings.json` and
  restore on launch. Quit persists before closing.
- `__main__.py` added so `python -m autoclicker` works.

### Icons
- Fixed the `power` glyph. The arc was `start=250, extent=70`, which drew a
  70 degree fragment near the top and rendered as a stray tick inside the Stop
  button. A power symbol is a near-full ring with a gap at 12 o'clock, so it is
  now `start=120, extent=300` plus a stem through the gap.
- Fixed the `loop` glyph. The arc gap sat on the right while the arrowhead was
  drawn at the top, so they did not meet. The gap and the arrowhead are now at
  the same angle.
- Re-centred the `click` and `chevron-right` glyphs, which were authored off
  to one side of the 28x28 box.
- Every catalog entry is now verified to stay inside its box and stay near the
  box centre. Directional glyphs (chevron-up, chevron-down) are the one
  deliberate exception.

## 2.0 - Neumorphism redesign

- Multi-card Neumorphism dashboard: soft dual shadows, low contrast, thin
  tracked typography, monochrome line-art icons, half-circle gauge.
- Cross-platform window icon (`.ico` on Windows, PNG or a runtime-generated
  PhotoImage elsewhere).
- Always-on-top re-asserted every 1.5 s for the root window and any tracked
  Toplevel.
- Wayland session warning on launch.
- Local venv with `scripts/setup.sh` and `scripts/run.sh`. No global packages.

## 1.0 - Initial release

- Basic clicker with CPS, countdown, and pause key.
- Help tooltips.
- CPS precision curve to offset CPU and interpreter overhead.
- SOLID structure.
