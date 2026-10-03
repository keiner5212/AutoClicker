# Autockicker

A cross-platform auto clicker with a Neumorphism UI.

- CPS control with a live dial readout.
- Countdown before clicking starts.
- Global pause hotkey (any `pynput` key name).
- Always-on-top with a toggle; re-asserted every 1.5 s so Linux window
  managers that drop the hint keep the window visible.
- Settings persist to a per-user JSON file.
- Neumorphism throughout: one surface color, dual soft shadows, inset
  wells, thin tracked type, monochrome line-art icons.

## Setup (venv only)

The project uses a local virtualenv. No global packages.

```bash
bash scripts/setup.sh   # creates .venv and installs pynput
bash scripts/run.sh     # activates the venv and runs the app
```

Or manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m autoclicker
```

## Linux notes

On Wayland, `pynput`'s mouse listener needs XWayland. Run with
`GDK_BACKEND=x11 bash scripts/run.sh`, or switch the session to X11.
The status badge shows `WAYLAND` on launch when it detects this.

## Config file

Settings are saved to `settings.json` in the per-user config directory:

- Windows: `%APPDATA%\AutoClicker\`
- Linux: `$XDG_CONFIG_HOME/AutoClicker/` (default `~/.config/AutoClicker/`)
- macOS: `~/Library/Application Support/AutoClicker/`

## Layout

```
+-------------------------------------------+
|  [dial card]        |  [settings card]   |
|  Clicker            |  CPS      [ 20 ] ? |
|  (gauge + CPS)      |  COUNTDOWN [  5 ] ? |
|                     |  PAUSE KEY [ f6 ] ? |
|  [status card]      |                    |
|  Status             |                    |
|  (IDLE, 00:00:00,   |                    |
|   TOP toggle)       |                    |
+-------------------------------------------+
|  [ Start ]  [ Stop ]              [ Quit ]|
+-------------------------------------------+
```

## Project layout

```
autoclicker/
  __init__.py            # entry point
  __main__.py            # enables `python -m autoclicker`
  core/
      AutoClickerApp.py   # orchestrator: validation, run state, settings
      Clicker.py          # the click loop and its CPS curve
      KeyboardListener.py # global pause hotkey
      platform_compat.py  # icon, always-on-top, session detection
      utils.py            # resource_path, config dir
  ui/
      theme.py            # palette, geometry, typography tokens
      widgets.py          # Neumorphic primitives + icon catalog
      dashboard.py        # two-column layout
scripts/
  setup.sh                # create venv and install deps
  run.sh                  # activate venv and run the app
  build.sh                # freeze the Linux executable with PyInstaller
autoclicker.spec          # PyInstaller build config, shared by every OS
requirements.txt          # pynput and Pillow
```

## Implementation notes

Tk has no antialiasing for Canvas items. The X11 core protocol draws a
rounded edge as a hard step from surface to fill, and no option changes
that. Text is the exception: Tk renders it through Xft and it is already
smooth.

So shapes are rasterised in `ui/render.py` with Pillow: draw at 4x, then
downscale with LANCZOS. Shadows are a real Gaussian blur of the shape's own
silhouette, offset in each direction. Text, tick labels, and the dial
readout stay as Canvas items because Xft already handles those.

Every render is cached, because a button repaints on each hover change.

Two earlier approaches were tried and both fought the design:

- `ttk.Entry` paints a themed border that `borderwidth=0` does not remove,
  so every field had a hard outline around the inset well. It is now
  `tk.Entry` with `relief="flat"`.
- Buttons that host a child `Frame` for their label get a rectangular
  background painted over the rounded pill, and the focus ring draws as a
  box. The button is now one Canvas: pill, icon, text, ring, and the whole
  hover/press target.

Tk arc angles also bite: 0 degrees is at 3 o'clock counting
counterclockwise, so a top half-dial is `start=0, extent=180`. The other
direction draws the bottom half.

One tkinter footgun worth knowing: `Misc._w` is the widget's Tk path name.
Assigning to `self._w` before `super().__init__()` looks fine and is
silently overwritten with a string.

## Roadmap

Macro support (ordered click and scroll steps at a set frequency, with
screen-point capture) was built and then removed. The macro engine and
recorder were deleted rather than left dangling. It is a clean re-add when
the compact UI is stable, because the current layout has room for one more
card.
