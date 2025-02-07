import threading
import time
from tkinter import ttk
from pynput.mouse import Controller, Button
from pynput import keyboard
from autoclicker.core.Tooltip import ToolTip
from autoclicker.core.utils import resource_path
import os


class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.clicking = False
        self.max_cps = 1000
        self.min_cps = 1
        self.mouse = Controller()
        self.window_title = "Auto Clicker"
        self.window_width = 330
        self.window_height = 210
        self.pause_key = keyboard.Key.alt_gr
        self.countdown_time = 5

        # Configurar estilo
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Segoe UI", 8), padding=3)
        self.style.configure("TLabel", font=("Segoe UI", 8))

        self.setup_ui()
        self.setup_keyboard_listener()

    def setup_ui(self):
        """Configura la interfaz de usuario."""
        self.root.title(self.window_title)
        self.root.geometry(f"{self.window_width}x{self.window_height}")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)
        self.root.configure(padx=8, pady=8)

        # Window icon
        try:
            self.root.iconbitmap(resource_path("icon.ico"))
        except Exception as e:
            pass

        # Crear grid layout
        self.root.grid_columnconfigure(1, weight=1)

        # Status label
        self.status_label = ttk.Label(
            self.root, text="Estado: Inactivo", anchor="center"
        )
        self.status_label.grid(row=0, column=0, columnspan=4, pady=3, sticky="ew")

        # Guide label
        self.guide_label = ttk.Label(
            self.root,
            text="Haz clic en 'Iniciar' para empezar. Pausa con la tecla especificada o con 'Detener'.",
            wraplength=self.window_width - 20,
        )
        self.guide_label.grid(row=1, column=0, columnspan=4, pady=5, sticky="ew")

        # CPS
        self.cps_label = ttk.Label(self.root, text="CPS:")
        self.cps_label.grid(row=2, column=0, pady=2, padx=3, sticky="e")
        self.cps_entry = ttk.Entry(self.root, width=15)
        self.cps_entry.insert(0, "20")
        self.cps_entry.grid(row=2, column=1, pady=2, sticky="w")

        self.cps_help = ttk.Button(self.root, text="?", width=2)
        self.cps_help.grid(row=2, column=2, padx=3)
        ToolTip(
            self.cps_help,
            """CPS significa 'Clics por segundo', ajusta este valor para controlar la frecuencia de los clics, el valor debe estar entre {} y {}. 

Nota: Los CPS son aproximados, ya que dependen de muchas cosas: cpu, interprete de python, tiempo de renderizacion, errores de redondeo del sistema IEEE 754, etc.
""".format(
                self.min_cps, self.max_cps
            ),
            200,
        )

        # Countdown
        self.countdown_label = ttk.Label(self.root, text="Countdown (s):")
        self.countdown_label.grid(row=3, column=0, pady=2, padx=3, sticky="e")
        self.countdown_entry = ttk.Entry(self.root, width=15)
        self.countdown_entry.insert(0, "5")
        self.countdown_entry.grid(row=3, column=1, pady=2, sticky="w")

        self.countdown_help = ttk.Button(self.root, text="?", width=2)
        self.countdown_help.grid(row=3, column=2, padx=3)
        ToolTip(
            self.countdown_help, "Tiempo de espera antes de iniciar (en segundos).", 200
        )

        # Tecla de pausa
        self.pause_key_label = ttk.Label(self.root, text="Tecla de pausa:")
        self.pause_key_label.grid(row=4, column=0, pady=2, padx=3, sticky="e")
        self.pause_key_entry = ttk.Entry(self.root, width=15)
        self.pause_key_entry.insert(0, "alt_gr")
        self.pause_key_entry.grid(row=4, column=1, pady=2, sticky="w")

        self.pause_key_help = ttk.Button(self.root, text="?", width=2)
        self.pause_key_help.grid(row=4, column=2, padx=3)
        ToolTip(
            self.pause_key_help,
            """Tecla para pausar el autoclicker (ej: alt_gr, ctrl, shift). 
El valor debe ser compatible con `pynput.keyboard.Key`. 
Para más información, consulta la documentación oficial: 
https://pynput.readthedocs.io/en/latest/keyboard.html#pynput.keyboard.Key""",
            200,
        )

        # Botones
        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=5, column=0, columnspan=4, pady=5)

        self.start_button = ttk.Button(
            button_frame, text="Iniciar", command=self.start_auto_clicker
        )
        self.start_button.pack(side="left", padx=3)

        self.stop_button = ttk.Button(
            button_frame, text="Detener", command=self.stop_clicking
        )
        self.stop_button.pack(side="left", padx=3)

        self.quit_button = ttk.Button(
            button_frame, text="Salir", command=self.root.quit
        )
        self.quit_button.pack(side="left", padx=3)

    def setup_keyboard_listener(self):
        """Inicia el listener del teclado."""
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def calculate_delay(self, cps):
        """Calcula el delay entre clics."""
        if cps < self.min_cps:
            return 1
        cps = min(cps, self.max_cps)

        res_time = 1 / cps
        # sustract 2% to avoid rounding errors and function call times
        return res_time * 0.98

    def start_clicking(self, cps):
        """Inicia el autoclicker."""
        self.clicking = True
        self.update_status("Estado: Ejecutando")

        delay = self.calculate_delay(cps)

        while self.clicking:
            self.mouse.click(Button.left)
            time.sleep(delay)

    def stop_clicking(self):
        """Detiene el autoclicker."""
        self.clicking = False
        self.update_status("Estado: Inactivo")

    def on_press(self, key):
        """Maneja la tecla de pausa."""
        if key == self.pause_key:
            self.update_status("Estado: Pausa")
            self.stop_clicking()

    def start_auto_clicker(self):
        """Inicia el autoclicker en un hilo separado."""
        try:
            cps = int(self.cps_entry.get())
            self.countdown_time = int(self.countdown_entry.get())
            self.pause_key = keyboard.Key[self.pause_key_entry.get()]
        except ValueError:
            self.update_status("Valor no válido")
            return
        except KeyError:
            self.update_status("Tecla no válida")
            return

        if cps <= 0:
            self.update_status("CPS debe ser mayor que 0")
            return

        threading.Thread(target=self.countdown).start()

    def countdown(self):
        """Muestra la cuenta regresiva en la interfaz."""
        self.update_status("Estado: Iniciando...")
        time.sleep(0.5)
        for i in range(self.countdown_time, 0, -1):
            self.update_status(f"Estado: Comienza en {i}s")
            time.sleep(1)

        # Iniciar el autoclicker después del countdown
        try:
            cps = int(self.cps_entry.get())
            threading.Thread(target=self.start_clicking, args=(cps,)).start()
        except ValueError:
            self.update_status("Error: CPS no válido")

    def update_status(self, message):
        """Actualiza el estado en la interfaz."""
        self.status_label.config(text=message)
