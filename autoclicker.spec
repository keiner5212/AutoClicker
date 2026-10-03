# PyInstaller configuration for AutoClicker.
#
# pynput loads its platform backend through importlib.import_module inside
# pynput/_util/__init__.py, so static analysis never sees it and a frozen
# build dies at startup with
# `ImportError: this platform is not supported: No module named 'pynput.keyboard._xorg'`.
# The backend module and its pynput._util helper have to be named by hand.
#
# Build with:  pyinstaller --clean autoclicker.spec
# Output name: AUTOCLICKER_NAME env var, default "autoclicker".

import os
import sys
from importlib.metadata import PackageNotFoundError, distribution

from PyInstaller.utils.hooks import copy_metadata


def project_metadata():
    """Ship the dist-info so the frozen app can read its own release version.

    Empty when the project is not installed in the build environment, which is
    the case for a plain `pip install -r requirements.txt` dev venv.
    """
    try:
        distribution("autoclicker")
    except PackageNotFoundError:
        return []
    return copy_metadata("autoclicker")


if sys.platform.startswith("linux"):
    backend = "xorg"
elif sys.platform == "darwin":
    backend = "darwin"
else:
    backend = "win32"

NAME = os.environ.get("AUTOCLICKER_NAME") or "autoclicker"

a = Analysis(
    ["autoclicker/__init__.py"],
    pathex=[],
    binaries=[],
    # icon.ico is loaded at runtime by AutoClickerApp._setup_window.
    datas=[("icon.ico", ".")] + project_metadata(),
    hiddenimports=[
        f"pynput.keyboard._{backend}",
        f"pynput.mouse._{backend}",
        f"pynput._util.{backend}",
        # Pillow reaches its Tk hook through a C extension and a meta path
        # finder that static analysis cannot see. Without both, the first
        # canvas blit raises `No module named 'PIL._tkinter_finder'`.
        "PIL._imagingtk",
        "PIL._tkinter_finder",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    # PyInstaller only honours an exe icon on Windows and macOS, and the macOS
    # build never had one. The window icon is set at runtime instead.
    icon="icon.ico" if sys.platform == "win32" else None,
)
