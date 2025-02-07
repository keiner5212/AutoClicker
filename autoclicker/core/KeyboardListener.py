from pynput import keyboard


class KeyboardListener:
    def __init__(self, app):
        self.app = app
        self.pause_key = keyboard.Key.alt_gr
        self.listener = None

    def start(self):
        """Inicia el listener del teclado."""
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def set_pause_key(self, key):
        """Establece la tecla de pausa."""
        self.pause_key = key

    def on_press(self, key):
        """Maneja la tecla de pausa."""
        if key == self.pause_key:
            self.app.ui.update_status("Estado: Pausa")
            self.app.clicker.stop()
