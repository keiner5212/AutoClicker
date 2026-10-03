## 2.0 - Neumorphism dashboard and macros

### Visual redesign
- Multi-card dashboard layout (header, two columns, footer) matching the
  Neumorphism reference image: soft dual shadows, low contrast, generous
  radius, thin tracked typography, monochrome line-art icons.
- New app header with the project name in a double-stroke thin font
  (lighter halo behind a darker fill).
- New dashboard widgets:
  - `NeumoIcon` with 20+ line-art icons drawn on a Canvas.
  - `NeumoSceneCard` for the small square "Single Click" / "Loop Click"
    shortcuts with a 56px icon well.
  - `NeumoListItem` for the soft inner rows used in the macro step list.
  - `NeumoAppHeader`, `NeumoCardTitle`, `NeumoPowerDot`, `NeumoChevron`.
  - `NeumoGauge` half-circle dial with 11 tick marks, animated needle,
    accent arc, and a center value readout.
- Responsive grid: at >= 800 px the window shows two columns; below
  that, columns stack. Right column is scrollable so the footer is
  always reachable.
- Subtle shadow stack: 10-step gradient, low offset (5 px), low alpha
  peak (0.55 dark / 0.85 light) for the soft, almost-imperceptible lift
  the reference uses.

### Macros
- Macro engine still runs ordered steps with click and scroll actions,
  per-step delay, loop toggle, and CPS override.
- Capture still records the next mouse click into a new step.
- Save / Load JSON in the user config directory; path shown in the
  dashboard event log.

### Cross-platform fixes
- App icon now loads on Windows (.ico), macOS, and Linux (PNG fallback
  or runtime-generated PhotoImage).
- Always-on-top re-asserted every 1.5s for the root window and any
  tracked Toplevel. Toggle button in the Status card flips the flag.
- Wayland session warning at startup explains the XWayland requirement.

### Setup
- Local venv only. `bash scripts/setup.sh` creates `.venv` and installs
  pynput. `bash scripts/run.sh` activates it and runs the app.
- No global Python packages required.

## 1.0 - Initial release

### Improvements
- Improvements to the user interface.
- Added inputs to configure the countdown, pause key, and CPS.
- Added help buttons.

### Fixes
- Attempted workaround for CPS precision issues using a relative curve.
- CPU usage optimizations.
- Followed SOLID principles.
