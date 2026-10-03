import os
import sys


def resource_path(relative_path):
    """Absolute path to a bundled resource. Works in dev and PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def user_config_dir(app_name="AutoClicker"):
    """Cross-platform per-user config directory.

    Windows: %APPDATA%\\<app_name>
    Linux:   ~/.config/<app_name>
    macOS:   ~/Library/Application Support/<app_name>
    """
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
            os.path.expanduser("~"), ".config"
        )
    path = os.path.join(base, app_name)
    os.makedirs(path, exist_ok=True)
    return path


def settings_path():
    return os.path.join(user_config_dir(), "settings.json")