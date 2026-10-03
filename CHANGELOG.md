# Changelog

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
