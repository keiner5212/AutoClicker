from tkinter import ttk
from autoclicker.core.Tooltip import ToolTip
from autoclicker.core.utils import resource_path


class AutoClickerUI:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Segoe UI", 8), padding=3)
        self.style.configure("TLabel", font=("Segoe UI", 8))

    def setup(self):
        """Configura la interfaz de usuario."""
        self.root.title(self.app.window_title)
        self.root.geometry(f"{self.app.window_width}x{self.app.window_height}")
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
            wraplength=self.app.window_width - 20,
        )
        self.guide_label.grid(row=1, column=0, columnspan=4, pady=5, sticky="ew")

        # CPS
        self.cps_label = ttk.Label(self.root, text="CPS:")
        self.cps_label.grid(row=2, column=0, pady=2, padx=3, sticky="e")
        self.cps_entry = ttk.Entry(self.root, width=20)  
        self.cps_entry.insert(0, "20")
        self.cps_entry.grid(row=2, column=1, pady=2, sticky="ew", padx=(0, 5))   

        self.cps_help = ttk.Button(self.root, text="?", width=2)
        self.cps_help.grid(row=2, column=2, padx=(0, 3), sticky="w")  

        ToolTip(
            self.cps_help,
            """CPS significa 'Clics por segundo', ajusta este valor para controlar la frecuencia de los clics, el valor debe estar entre {} y {}. 

Nota: Los CPS son aproximados, ya que dependen de muchas cosas: cpu, interprete de python, tiempo de renderizacion, errores de redondeo del sistema IEEE 754, etc.
""".format(
                1, 1000
            ),
            250,
        )

        # Countdown
        self.countdown_label = ttk.Label(self.root, text="Countdown (s):")
        self.countdown_label.grid(row=3, column=0, pady=2, padx=3, sticky="e")
        self.countdown_entry = ttk.Entry(self.root, width=20)  
        self.countdown_entry.insert(0, "5")
        self.countdown_entry.grid(row=3, column=1, pady=2, sticky="ew", padx=(0, 5)) 

        self.countdown_help = ttk.Button(self.root, text="?", width=2)
        self.countdown_help.grid(row=3, column=2, padx=(0, 3), sticky="w")  

        ToolTip(
            self.countdown_help, "Tiempo de espera antes de iniciar (en segundos).", 200
        )

        # Tecla de pausa
        self.pause_key_label = ttk.Label(self.root, text="Tecla de pausa:")
        self.pause_key_label.grid(row=4, column=0, pady=2, padx=3, sticky="e")
        self.pause_key_entry = ttk.Entry(self.root, width=20)  
        self.pause_key_entry.insert(0, "alt_gr")
        self.pause_key_entry.grid(row=4, column=1, pady=2, sticky="ew", padx=(0, 5)) 

        self.pause_key_help = ttk.Button(self.root, text="?", width=2)
        self.pause_key_help.grid(row=4, column=2, padx=(0, 3), sticky="w")  

        ToolTip(
            widget=self.pause_key_help,
            text="""Tecla para pausar el autoclicker (ej: alt_gr, ctrl, shift). 
El valor debe ser compatible con `pynput.keyboard.Key`. 
Para más información, consulta la documentación oficial: 
https://pynput.readthedocs.io/en/latest/keyboard.html#pynput.keyboard.Key, dale click a este boton para abrir la documentación.""",
            link="https://pynput.readthedocs.io/en/latest/keyboard.html#pynput.keyboard.Key",
            wraplength=250,
        )

        # Botones
        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=5, column=0, columnspan=4, pady=5)

        self.start_button = ttk.Button(
            button_frame, text="Iniciar", command=self.app.start_auto_clicker
        )
        self.start_button.pack(side="left", padx=3)

        self.stop_button = ttk.Button(
            button_frame, text="Detener", command=self.app.stop_clicking
        )
        self.stop_button.pack(side="left", padx=3)

        self.quit_button = ttk.Button(
            button_frame, text="Salir", command=self.root.quit
        )
        self.quit_button.pack(side="left", padx=3)

    def update_status(self, message):
        """Actualiza el estado en la interfaz."""
        self.status_label.config(text=message)