# Autockicker

A cross-platform auto clicker with a Neumorphism UI and a programmable
macro engine for ordered click and scroll sequences.

- Basic clicker: CPS, pause hotkey, countdown.
- Macro engine: ordered steps with action (left/right/middle click or
  scroll), x/y, per-step delay, loop toggle, CPS override.
- One-shot mouse capture: press Capture, then click anywhere on screen
  to record the next step.
- Save / load macros as JSON in the user config directory.
- Neumorphism dashboard: multi-card layout, soft dual shadows, low
  contrast, thin tracked typography, monochrome line-art icons, a
  half-circle gauge with animated needle.
- Cross-platform: Windows, macOS, Linux (X11 and XWayland).

## Setup (venv only)

The project uses a local virtualenv. No global packages.

```bash
bash scripts/setup.sh   # creates .venv and installs pynput
bash scripts/run.sh     # activates venv and runs the app
```

Or manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m autoclicker
```

## Linux notes

On Wayland, pynput's mouse listener needs XWayland. Run with
`GDK_BACKEND=x11 bash scripts/run.sh`, or switch your session to X11,
for click and capture to register. The warning appears on launch.

## Project layout

```
autoclicker/
  __init__.py            # entry point
  core/
      AutoClickerApp.py   # orchestrator + dashboard glue
      Clicker.py          # basic click loop
      KeyboardListener.py # global pause hotkey
      MacroEngine.py      # ordered step runner
      MacroRecorder.py    # one-shot mouse capture
      platform_compat.py  # icon, always-on-top, session detection
      utils.py            # resource_path, config dir
  ui/
      theme.py            # palette, geometry, typography tokens
      widgets.py          # Neumorphic primitives + icon catalog
      dashboard.py        # responsive 2-column dashboard layout
scripts/
  setup.sh                # create venv and install deps
  run.sh                  # activate venv and run the app
requirements.txt          # pynput only
```