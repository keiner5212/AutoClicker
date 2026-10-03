import threading
import time
from pynput.mouse import Button


class Clicker:
    def __init__(self, mouse, app):
        self.mouse = mouse
        self.app = app
        self.clicking = False
        self.cps = 0
        self._started_at = None

    def start(self, cps):
        """Inicia el autoclicker."""
        self.cps = cps
        self.clicking = True
        self._started_at = time.monotonic()
        self._on_start()

        delay = self.calculate_delay(cps)
        next_click = time.monotonic()
        while self.clicking:
            self.mouse.click(Button.left)
            next_click += delay
            # Sleep in slices so stop() is responsive at high CPS.
            while self.clicking and time.monotonic() < next_click:
                time.sleep(min(0.01, max(0.0, next_click - time.monotonic())))
            # If we fell behind, resync instead of drifting.
            if next_click < time.monotonic() - delay:
                next_click = time.monotonic()

    def stop(self):
        """Detiene el autoclicker."""
        self.clicking = False

    def _on_start(self):
        # Hop to the Tk thread: pynput's controller and our worker both run
        # off the main loop, and touching widgets from here is unsafe.
        self.app.post_to_ui(self._on_start_on_ui)

    def _on_start_on_ui(self):
        self.app._pending_start = False
        self.app.dashboard.set_state("RUNNING", self.app.ui_success())
        self.app.dashboard.set_running(True)

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
        """Muestra la cuenta regresiva y luego arranca el clicker."""
        self.app.post_to_ui(
            lambda: self.app.dashboard.set_state("ARMING", self.app.ui_paused())
        )
        time.sleep(0.4)
        for i in range(countdown_time, 0, -1):
            if not self.app._pending_start:
                return
            self.app.post_to_ui(
                lambda n=i: self.app.dashboard.set_state(
                    f"IN {n}s", self.app.ui_paused()
                )
            )
            time.sleep(1)
        if not self.app._pending_start:
            return
        self.app._pending_start = False
        threading.Thread(target=self.start, args=(cps,), daemon=True).start()
