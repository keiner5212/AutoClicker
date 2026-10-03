import threading
import time
from pynput.mouse import Button

# Weight of the newest interval in the running average of the gap between
# clicks. The loop keeps an absolute deadline, so the true gap is near
# constant and a short average tracks a real stall within a few clicks while
# staying steady enough for the dial needle not to twitch.
RATE_SMOOTHING = 0.2


class Clicker:
    def __init__(self, mouse, app):
        self.mouse = mouse
        self.app = app
        self.clicking = False
        self.cps = 0
        self._started_at = None
        self._interval_avg = 0.0
        self._last_click_at = None

    @property
    def started_at(self):
        return self._started_at

    @property
    def measured_cps(self):
        """Delivered rate from the observed gaps, 0 until a click lands.

        Read by the main loop while the click thread writes it. Each field is
        a single float or None, so a read sees one write or the other, never
        a mix, and a stale value for one sample is harmless.
        """
        if self._interval_avg <= 0.0:
            return 0.0
        return 1.0 / self._interval_avg

    def _record_click(self, at):
        if self._last_click_at is None:
            self._last_click_at = at
            return
        gap = at - self._last_click_at
        if gap > 0.0:
            if self._interval_avg <= 0.0:
                self._interval_avg = gap
            else:
                self._interval_avg += RATE_SMOOTHING * (gap - self._interval_avg)
        self._last_click_at = at

    def start(self, cps):
        """Inicia el autoclicker."""
        self.cps = cps
        self.clicking = True
        self._started_at = time.monotonic()
        self._interval_avg = 0.0
        self._last_click_at = self._started_at
        self._on_start()

        delay = self.calculate_delay(cps)
        # Absolute deadline: the next click is due one period from now, so
        # per-iteration sleep overshoot cannot accumulate into drift. The
        # first click waits a full period too. Firing it at t=0 put one click
        # ahead of the schedule, and a counter reading the first second of a
        # run read 21 at 20 CPS.
        next_click = time.monotonic() + delay
        while self.clicking:
            now = time.monotonic()
            if now < next_click:
                # Sleep in slices so stop() is responsive at high CPS.
                time.sleep(min(0.01, next_click - now))
                continue
            self.mouse.click(Button.left)
            self._record_click(time.monotonic())
            next_click += delay
            # Fell a whole period behind, which only happens when a click
            # cost more than the period. Re-base one period ahead of now:
            # re-basing onto the current instant drops the period the user
            # asked for, and skipping forward over every missed period fires
            # a burst of catch-up clicks nobody requested.
            if next_click <= time.monotonic() - delay:
                next_click = time.monotonic() + delay

    def stop(self):
        """Detiene el autoclicker."""
        self.clicking = False
        self._interval_avg = 0.0
        self._last_click_at = None

    def _on_start(self):
        # Hop to the Tk thread: pynput's controller and our worker both run
        # off the main loop, and touching widgets from here is unsafe.
        self.app.post_to_ui(self._on_start_on_ui)

    def _on_start_on_ui(self):
        self.app.dashboard.set_state("RUNNING", self.app.ui_success())
        self.app.dashboard.set_running(True)

    def calculate_delay(self, cps):
        """Seconds between clicks for a requested rate in clicks per second.

        The period is 1/cps, so the delivered rate is 1/period = cps. The old
        quadratic scaled the period by a percentage below 1, which made the
        switch deliver cps/percentage(cps) instead: 20 was requested and 21.05
        arrived, 70 was requested and 82.9 arrived. The cost of a click is
        charged against the sleep budget inside each period, not against the
        period itself, so no compensation term belongs here.
        """
        if cps < 1:
            return 1
        return 1.0 / cps

    def countdown(self, countdown_time, cps):
        """Muestra la cuenta regresiva y luego arranca el clicker."""
        self.app.post_to_ui(
            lambda: self.app.dashboard.set_state("ARMING", self.app.ui_paused())
        )
        time.sleep(0.4)
        for i in range(countdown_time, 0, -1):
            if self.app.stop_requested:
                self.app.end_run()
                return
            self.app.post_to_ui(
                lambda n=i: self.app.dashboard.set_state(
                    f"IN {n}s", self.app.ui_paused()
                )
            )
            time.sleep(1)
        if self.app.stop_requested:
            self.app.end_run()
            return
        threading.Thread(target=self.start, args=(cps,), daemon=True).start()
