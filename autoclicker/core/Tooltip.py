import tkinter as tk
import webbrowser


class ToolTip:
    def __init__(self, widget, text, wraplength=200, link=None):
        self.widget = widget
        self.text = text
        self.link = link
        self.tooltip = None
        self.wraplength = wraplength

        # Event for showing the tooltip
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.attributes("-topmost", True)

        screen_width = self.tooltip.winfo_screenwidth()
        screen_height = self.tooltip.winfo_screenheight()

        x = event.x_root + 10
        y = event.y_root + 10

        if x + self.wraplength > screen_width:
            x = screen_width - self.wraplength - 10
        if y + 50 > screen_height:
            y = screen_height - 50 - 10

        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            self.tooltip,
            text=self.text,
            background="light yellow",
            relief="solid",
            bd=1,
            wraplength=self.wraplength,
        )
        label.pack(padx=5, pady=5)

        # If there's a link, bind the click event to open it
        if self.link:
            self.widget.bind("<Button-1>", self.open_link)

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()

    def open_link(self, event):
        if self.link:
            webbrowser.open(self.link)