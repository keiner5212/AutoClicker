"""AutoClicker entry point."""

import sys

import tkinter as tk

from autoclicker.buildinfo import build_info, main as _build_main


def main():
    # `--build` reports the fingerprint of the running source and exits.
    if _build_main(sys.argv[1:]) == 0:
        return

    from autoclicker.core.AutoClickerApp import AutoClickerApp

    # Named before the window opens: if the title bar does not match
    # `python -m autoclicker --build`, two different code trees are involved.
    root = tk.Tk()
    app = AutoClickerApp(root)
    try:
        root.mainloop()
    finally:
        if not app._closed:
            app._on_close()


if __name__ == "__main__":
    main()
