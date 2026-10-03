"""Cross-platform helpers: window icon, always-on-top, session detection.

Centralizes the differences between Windows, macOS, and Linux/Wayland so the
rest of the app stays system-agnostic.
"""

import os
import sys
import tkinter as tk

from autoclicker.ui import theme

TOPLEVEL_REFRESH_MS = 1500


def detect_session():
    """Return 'wayland', 'x11', 'windows', 'macos', or 'other'."""
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    session = os.environ.get("XDG_SESSION_TYPE", "").lower()
    if session == "wayland" or bool(os.environ.get("WAYLAND_DISPLAY")):
        return "wayland"
    if session == "x11" or bool(os.environ.get("DISPLAY")):
        return "x11"
    return "other"


def session_warning():
    """Short human-readable hint when pynput may be limited."""
    session = detect_session()
    if session == "wayland":
        return (
            "Wayland detected. pynput needs XWayland; run with "
            "GDK_BACKEND=x11 or disable Wayland for full input capture."
        )
    if session == "other":
        return "No display server detected; pynput input capture will not start."
    return ""


def _build_photo_icon(master, size=32):
    """Build a small PhotoImage icon at runtime as a safe cross-platform fallback."""
    photo = tk.PhotoImage(master=master, width=size, height=size)
    bg = theme.ACCENT
    accent_alt = theme.ACCENT_ALT
    fg = theme.SURFACE
    for y in range(size):
        for x in range(size):
            photo.put(bg, (x, y))
    for y in range(6, 26):
        for x in range(11, 21):
            photo.put(accent_alt, (x, y))
    for y in range(6, 26):
        for x in range(12, 20):
            photo.put(fg, (x, y))
    return photo


def apply_window_icon(root, icon_path=None):
    """Apply the app icon on Windows, macOS, and Linux without raising.

    - Windows: tries iconbitmap if an .ico exists.
    - Linux/macOS: uses iconphoto with a PNG file if found, otherwise a
      PhotoImage generated at runtime so the window always has a badge.
    """
    if root is None:
        return None

    try:
        if icon_path and sys.platform.startswith("win") and icon_path.lower().endswith(".ico"):
            try:
                root.iconbitmap(icon_path)
                return None
            except Exception:
                pass

        png_candidate = None
        if icon_path:
            base, _ext = os.path.splitext(icon_path)
            for cand in (icon_path, base + ".png"):
                if os.path.exists(cand):
                    png_candidate = cand
                    break
        if png_candidate:
            try:
                photo = tk.PhotoImage(file=png_candidate, master=root)
                root.iconphoto(True, photo)
                return photo
            except Exception:
                pass

        photo = _build_photo_icon(root)
        root.iconphoto(True, photo)
        return photo
    except Exception:
        return None


class AlwaysOnTopEnforcer:
    """Re-assert `-topmost` periodically for the root and any tracked Toplevel.

    Tk drops the topmost hint under some Linux window managers when another
    window is focused. Re-asserting every ~1.5s keeps the app above normal
    windows while staying polite to fullscreen apps on other desktops.
    """

    def __init__(self, root, refresh_ms=TOPLEVEL_REFRESH_MS):
        self.root = root
        self.refresh_ms = refresh_ms
        self._tracked = []
        self._after_id = None
        self._stopped = False

    def start(self):
        self._stopped = False
        self._assert()
        self._schedule()

    def stop(self):
        self._stopped = True
        if self._after_id is not None:
            try:
                self.root.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def track(self, toplevel):
        """Add a Toplevel to the enforcement set (e.g. tooltip popovers)."""
        if toplevel is not None and toplevel not in self._tracked:
            self._tracked.append(toplevel)
        self._assert(toplevel)

    def untrack(self, toplevel):
        if toplevel in self._tracked:
            self._tracked.remove(toplevel)

    def _assert(self, widget=None):
        target = widget or self.root
        try:
            target.wm_attributes("-topmost", True)
        except Exception:
            pass
        if sys.platform.startswith("win"):
            try:
                target.wm_attributes("-toolwindow", False)
            except Exception:
                pass

    def _schedule(self):
        if self._stopped:
            return
        for w in (self.root, *self._tracked):
            if w is not None:
                try:
                    if w.winfo_exists():
                        self._assert(w)
                except Exception:
                    pass
        try:
            self._after_id = self.root.after(self.refresh_ms, self._schedule)
        except Exception:
            self._after_id = None