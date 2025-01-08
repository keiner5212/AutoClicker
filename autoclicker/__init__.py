import tkinter as tk
from tkinter import ttk
from pynput.mouse import Controller, Button
from pynput import keyboard
import threading
import time
from autoclicker.core.Tooltip import ToolTip

# Global variables
clicking = False
max_cps = 1000
min_cps = 1
mouse = Controller()
window_title = "Auto Clicker"
window_width = 350
window_height = 200


def main():
    def calculate_delay(cps):
        """Calculate the delay between clicks based on the CPS,
        if it's less than min_cps, return 1 second,
        if it's greater than max_cps, return 1/max_cps second."""
        if cps < min_cps:
            return 1
        cps = min(cps, max_cps)
        return 1 / cps

    def start_clicking(cps):
        time.sleep(5.7)  # start after countdown
        global clicking
        clicking = True
        update_status("Estado: Ejecutando")

        delay = calculate_delay(cps)

        start_time = time.perf_counter()  # get the current time
        next_click_time = start_time + delay  # calculate the time for the first click

        while clicking:
            current_time = time.perf_counter()  # get the current time
            if current_time >= next_click_time:
                # if the current time is greater than or equal to the next click time
                # then click the mouse and recalculate the next click time
                mouse.click(Button.left)
                next_click_time = current_time + delay

    def stop_clicking():
        global clicking
        clicking = False

    def on_press(key):
        if key == keyboard.Key.alt_gr:  # Pause with AltGr
            update_status("Estado: Pausa")
            stop_clicking()

    def start_auto_clicker():
        try:
            cps = int(cps_entry.get())
        except ValueError:
            update_status("CPS no válido")
            return
        if cps <= 0:
            update_status("CPS debe ser mayor que 0")
            return

        threading.Thread(target=countdown, args=(5,)).start()
        threading.Thread(target=start_clicking, args=(cps,)).start()

    def countdown(seconds):
        update_status("Estado: Iniciando...")
        time.sleep(0.5)
        for i in range(seconds, 0, -1):
            update_status(f"Estado: Comienza en {i}s")
            time.sleep(1)

    def update_status(message):
        status_label.config(text=message)

    # Main window
    root = tk.Tk()
    root.title(window_title)
    root.geometry(f"{window_width}x{window_height}")
    root.attributes("-topmost", True)  # Always on top
    root.resizable(False, False)  # Disable resizing
    root.configure(padx=10, pady=10)

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    try:
        root.iconbitmap("icon.ico")
    except Exception as e:
        print("Error al cargar el icono:", e)

    # TTK theme
    style = ttk.Style()
    style.configure("TButton", font=("Segoe UI", 8), padding=5)
    style.configure("TLabel", font=("Segoe UI", 8))

    # Status label
    status_label = ttk.Label(root, text="Estado: Inactivo", anchor="e")
    status_label.grid(row=0, column=0, columnspan=3, pady=5)

    # guide label
    label = ttk.Label(
        root,
        text="Haz clic en 'Iniciar' para empezar a hacer clics, pausa con AltGr o con el boton \"Detener\".",
        wraplength=window_width - 20,
    )
    label.grid(row=1, column=0, columnspan=3, pady=10)

    # CPS entry label
    min_cps, max_cps = 1, 100
    cps_label = ttk.Label(
        root,
        text="CPS:",
        wraplength=window_width - 20,
    )
    cps_label.grid(row=3, column=0, pady=10, padx=10)

    # CPS entry
    cps_entry = ttk.Entry(root)
    cps_entry.insert(0, "20")
    cps_entry.grid(row=3, column=1, padx=10, pady=5)

    # Help button
    help_button = ttk.Button(root, text="?", width=3)
    help_button.grid(row=3, column=2, padx=10, pady=5)

    # Buttons
    start_button = ttk.Button(root, text="Iniciar", command=start_auto_clicker)
    start_button.grid(row=4, column=0, pady=10)

    stop_button = ttk.Button(
        root,
        text="Detener",
        command=lambda: [stop_clicking(), update_status("Inactivo")],
    )
    stop_button.grid(row=4, column=1, pady=10)

    quit_button = ttk.Button(root, text="Salir", command=root.quit)
    quit_button.grid(row=4, column=2, pady=10)

    tooltip = ToolTip(
        help_button,
        """CPS significa 'Clics por segundo', ajusta este valor para controlar la frecuencia de los clics, el valor debe estar entre {} y {}. 
        
        Nota: Los CPS son aproximados, ya que dependen de muchas cosas: cpu, interprete de python, tiempo de renderizacion, errores de redondeo del sistema IEEE 754, etc.""".format(
            min_cps, max_cps
        ),
        300,
    )

    root.mainloop()
    listener.stop()


if __name__ == "__main__":
    main()