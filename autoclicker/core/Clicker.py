import threading
import time
from pynput.mouse import Button

class Clicker:
    def __init__(self, mouse, app):
        self.mouse = mouse
        self.app = app
        self.clicking = False

    def start(self, cps):
        """Inicia el autoclicker."""
        self.clicking = True
        self.app.ui.update_status("Estado: Ejecutando")

        delay = self.calculate_delay(cps)

        while self.clicking:
            self.mouse.click(Button.left)
            time.sleep(delay)

    def stop(self):
        """Detiene el autoclicker."""
        self.clicking = False

    def calculate_delay(self, cps):
        """Calcula el delay entre clics usando una curva cuadrática ajustada."""
        if cps < 1:
            return 1
        cps = min(cps, 500)  

        # coeficientes de la curva cuadrática
        a = 2.634e-6  
        b = -0.002351
        c = 0.996
        percentage = a * (cps ** 2) + b * cps + c
        percentage = max(min(percentage, 0.95), 0.5)
        delay = (1 / cps) * percentage
        return delay

    def countdown(self, countdown_time, cps):
        """Muestra la cuenta regresiva en la interfaz."""
        self.app.ui.update_status("Estado: Iniciando...")
        time.sleep(0.5)
        for i in range(countdown_time, 0, -1):
            self.app.ui.update_status(f"Estado: Comienza en {i}s")
            time.sleep(1)

        threading.Thread(target=self.start, args=(cps,)).start()
