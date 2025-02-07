import threading
from pynput.mouse import Controller
from pynput import keyboard
from autoclicker.core.AutoClickerUI import AutoClickerUI
from autoclicker.core.KeyboardListener import KeyboardListener
from autoclicker.core.Clicker import Clicker


class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.clicking = False
        self.mouse = Controller()
        self.window_title = "Auto Clicker"
        self.window_width = 330
        self.window_height = 210

        self.ui = AutoClickerUI(self.root, self)
        self.keyboard_listener = KeyboardListener(self)
        self.clicker = Clicker(self.mouse, self)

        self.setup_ui()
        self.keyboard_listener.start()

    def setup_ui(self):
        """Configura la interfaz de usuario."""
        self.ui.setup()

    def start_auto_clicker(self):
        """Inicia el autoclicker en un hilo separado."""
        try:
            cps = int(self.ui.cps_entry.get())
            countdown_time = int(self.ui.countdown_entry.get())
            pause_key = keyboard.Key[self.ui.pause_key_entry.get()]
        except ValueError:
            self.ui.update_status("Valor no válido")
            return
        except KeyError:
            self.ui.update_status("Tecla no válida")
            return

        if cps <= 0:
            self.ui.update_status("CPS debe ser mayor que 0")
            return

        self.keyboard_listener.set_pause_key(pause_key)
        threading.Thread(target=self.clicker.countdown, args=(countdown_time, cps)).start()

    def stop_clicking(self):
        """Detiene el autoclicker."""
        self.clicker.stop()
        self.ui.update_status("Estado: Inactivo")