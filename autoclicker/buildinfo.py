"""Identifies which build of the code is actually running.

A screenshot cannot show whether a process is running the current source or a
stale copy, a cached bytecode file, or a different checkout. This prints a
short fingerprint of the UI sources at import time so the running build is
verifiable from the outside: `python -m autoclicker --build` writes it to
stdout and stderr, and the app also shows it in the window title.

The stamp changes whenever any UI source changes, so a mismatch between the
title bar and a fresh `--build` run means the two are not the same code.
"""

import hashlib
import os
import sys
from importlib.metadata import PackageNotFoundError, version as _dist_version

_HERE = os.path.dirname(os.path.abspath(__file__))
_SOURCES = (
    os.path.join(_HERE, "ui", "widgets.py"),
    os.path.join(_HERE, "ui", "render.py"),
    os.path.join(_HERE, "ui", "dashboard.py"),
    os.path.join(_HERE, "ui", "theme.py"),
    os.path.join(_HERE, "core", "AutoClickerApp.py"),
)


def _detect_version():
    """Release version from the installed distribution, which is pyproject's.

    "dev" means the project is not installed, so there is no release version to
    report. The spec copies the metadata into the frozen build.
    """
    try:
        return _dist_version("autoclicker")
    except PackageNotFoundError:
        return "dev"


VERSION = _detect_version()


def build_stamp():
    """Short fingerprint of the UI sources, or a marker if unreadable."""
    digest = hashlib.sha256()
    for path in _SOURCES:
        try:
            with open(path, "rb") as handle:
                digest.update(handle.read())
        except OSError:
            return "unreadable"
    return digest.hexdigest()[:8]


def build_info():
    return f"v{VERSION} build {build_stamp()}"


def main(argv=None):
    """Entry point. `--build` prints the fingerprint and exits."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "--build":
        info = build_info()
        sys.stdout.write(info + "\n")
        sys.stderr.write(info + "\n")
        return 0
    return None
