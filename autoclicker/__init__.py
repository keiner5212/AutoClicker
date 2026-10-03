"""AutoClicker entry point."""

import tkinter as tk

from autoclicker.core.AutoClickerApp import AutoClickerApp


def main():
    root = tk.Tk()
    app = AutoClickerApp(root)
    try:
        root.mainloop()
    finally:
        if not app._closed:
            app._on_close()


if __name__ == "__main__":
    main()