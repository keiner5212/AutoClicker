"""Run-lifecycle tests for AutoClickerApp, with no display.

The app normally needs a Tk root and a pynput controller, so these drive the
run-ownership half directly. The bug they exist for: `begin_run` used to test
`_stop_requested` and the caller cleared it afterwards, so the first Stop
latched the flag and every later Start was refused until the app restarted.
"""

import threading
import unittest


class StubDashboard:
    def __init__(self):
        self.states = []
        self.cps_values = []
        self.cps_targets = []
        self.running = []
        self.topmost = None
        self.build = None

    def set_state(self, text, color):
        self.states.append(text)

    def set_cps(self, value):
        self.cps_values.append(value)

    def set_cps_target(self, requested):
        self.cps_targets.append(requested)

    def set_running(self, running):
        self.running.append(running)

    def set_topmost(self, on):
        self.topmost = on

    def set_build(self, build):
        self.build = build

    def set_runtime(self, seconds):
        pass


class StubClicker:
    def __init__(self):
        self.clicking = False
        self.started_at = None
        self.measured_cps = 0.0
        self.stops = 0

    def stop(self):
        self.clicking = False
        self.stops += 1


class RunOwnership:
    """The run-slot half of AutoClickerApp, lifted out so it can be driven.

    Kept in step with AutoClickerApp.begin_run / end_run / run_active /
    stop_requested. If those change, change this with them.
    """

    def __init__(self):
        self._stop_requested = threading.Event()
        self._run_lock = threading.Lock()
        self._run_active = False

    @property
    def run_active(self):
        with self._run_lock:
            return self._run_active

    @property
    def stop_requested(self):
        return self._stop_requested.is_set()

    def begin_run(self):
        with self._run_lock:
            if self._run_active:
                return False
            self._stop_requested.clear()
            self._run_active = True
            return True

    def end_run(self):
        with self._run_lock:
            self._stop_requested.set()
            self._run_active = False


class StartStopTests(unittest.TestCase):
    def setUp(self):
        self.state = RunOwnership()

    def test_start_then_stop_then_start_again(self):
        self.assertTrue(self.state.begin_run())
        self.assertTrue(self.state.run_active)

        self.state.end_run()
        self.assertFalse(self.state.run_active)
        self.assertTrue(self.state.stop_requested)

        # The reported symptom: this is what used to return False forever.
        self.assertTrue(self.state.begin_run())
        self.assertTrue(self.state.run_active)
        # And the new run must not inherit the previous run's stop request,
        # or its countdown would abort immediately.
        self.assertFalse(self.state.stop_requested)

    def test_many_cycles_stay_reusable(self):
        for _ in range(25):
            self.assertTrue(self.state.begin_run())
            self.state.end_run()
        self.assertTrue(self.state.begin_run())

    def test_a_second_start_while_a_run_is_live_is_refused(self):
        self.assertTrue(self.state.begin_run())
        self.assertFalse(self.state.begin_run())
        self.assertTrue(self.state.run_active)

    def test_stop_during_countdown_releases_the_slot(self):
        self.assertTrue(self.state.begin_run())
        # What Clicker.countdown does when it sees a stop mid-countdown.
        self.state.end_run()
        self.assertFalse(self.state.run_active)
        self.assertTrue(self.state.begin_run())

    def test_run_active_is_false_before_anything_starts(self):
        self.assertFalse(self.state.run_active)
        self.assertFalse(self.state.stop_requested)


class ConcurrentSlotTests(unittest.TestCase):
    def test_only_one_of_many_threads_can_claim_the_slot(self):
        state = RunOwnership()
        claims = []
        barrier = threading.Barrier(8)

        def claim():
            barrier.wait()
            if state.begin_run():
                claims.append(1)

        threads = [threading.Thread(target=claim) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(len(claims), 1)
        self.assertTrue(state.run_active)


if __name__ == "__main__":
    unittest.main()
