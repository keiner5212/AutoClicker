"""Pacing checks for Clicker, with no mouse and no display.

The loop is driven by a fake clock patched over `time.monotonic` and
`time.sleep`, and the click only advances that clock. An interval shorter
than the requested period is then a real defect in the deadline logic and
not OS scheduler noise.
"""

import unittest
from unittest import mock

from autoclicker.core.Clicker import Clicker


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += max(seconds, 0.0)

    def advance(self, seconds):
        self.now += seconds


class StubMouse:
    """Charges a fixed cost per click against the clock."""

    def __init__(self, clock, cost):
        self.clock = clock
        self.cost = cost
        self.times = []

    def click(self, button):
        self.times.append(self.clock.now)
        self.clock.advance(self.cost)


class StubApp:
    stop_requested = False

    def post_to_ui(self, _fn):
        pass

    def ui_paused(self):
        return None

    def ui_success(self):
        return None

    def clear_stop_request(self):
        type(self).stop_requested = False


def run_loop(cps, cost, count, stall_after=None, stall_for=0.0):
    """Drive Clicker.start on a fake clock and return the click timestamps."""
    clock = FakeClock()
    mouse = StubMouse(clock, cost)
    clicker = Clicker(mouse, StubApp())
    state = {"stalled": False}

    def click(button):
        original = StubMouse.click
        original(mouse, button)
        if (
            stall_after is not None
            and not state["stalled"]
            and len(mouse.times) == stall_after
        ):
            state["stalled"] = True
            clock.advance(stall_for)
        if len(mouse.times) >= count:
            clicker.stop()

    mouse.click = click
    with mock.patch("autoclicker.core.Clicker.time") as fake_time:
        fake_time.monotonic = clock.monotonic
        fake_time.sleep = clock.sleep
        clicker.start(cps)
    return mouse.times


class DelayLawTests(unittest.TestCase):
    def test_period_is_the_reciprocal_of_the_requested_rate(self):
        clicker = Clicker(StubMouse(FakeClock(), 0.0), StubApp())
        for cps in (1, 5, 20, 70, 200, 1000):
            with self.subTest(cps=cps):
                self.assertAlmostEqual(clicker.calculate_delay(cps), 1.0 / cps)
                self.assertAlmostEqual(
                    1.0 / clicker.calculate_delay(cps), cps, places=9
                )


class PacingTests(unittest.TestCase):
    def test_delivered_rate_matches_request(self):
        for cps, cost in ((20, 0.0), (20, 0.001), (70, 0.0), (70, 0.001)):
            with self.subTest(cps=cps, cost=cost):
                times = run_loop(cps, cost, 400)
                measured = (len(times) - 1) / (times[-1] - times[0])
                self.assertAlmostEqual(measured / cps, 1.0, delta=0.01)

    def test_no_interval_falls_short_of_the_period(self):
        for cps, cost in ((20, 0.0), (70, 0.001), (200, 0.0005)):
            with self.subTest(cps=cps, cost=cost):
                times = run_loop(cps, cost, 300)
                period = 1.0 / cps
                for earlier, later in zip(times, times[1:]):
                    self.assertGreaterEqual(later - earlier, period - 1e-9)

    def test_first_interval_is_one_period(self):
        times = run_loop(20, 0.0, 5)
        self.assertAlmostEqual(times[1] - times[0], 0.05, places=9)

    def test_a_stall_rebases_one_period_instead_of_bursting(self):
        times = run_loop(20, 0.0, 60, stall_after=10, stall_for=0.5)
        gaps = [b - a for a, b in zip(times, times[1:])]
        # One gap absorbs the 0.5s stall; none collapses into a catch-up burst.
        self.assertEqual(sum(1 for g in gaps if g < 0.049), 0)
        self.assertEqual(sum(1 for g in gaps if g > 0.1), 1)


def run_measured(cps, cost, count, stall_after=None, stall_for=0.0):
    """Run the loop and return the reported rate after each click."""
    clock = FakeClock()
    mouse = StubMouse(clock, cost)
    clicker = Clicker(mouse, StubApp())
    readings = []
    state = {"stalled": False}

    def click(button):
        StubMouse.click(mouse, button)
        clicker._record_click(clock.now)
        if (
            stall_after is not None
            and not state["stalled"]
            and len(mouse.times) == stall_after
        ):
            state["stalled"] = True
            clock.advance(stall_for)
            clicker._record_click(clock.now)
        readings.append(clicker.measured_cps)
        if len(mouse.times) >= count:
            clicker.stop()

    mouse.click = click
    with mock.patch("autoclicker.core.Clicker.time") as fake_time:
        fake_time.monotonic = clock.monotonic
        fake_time.sleep = clock.sleep
        clicker.start(cps)
    return readings


def feed_intervals(gaps):
    """Drive the estimator from a synthetic gap series, no pacing loop.

    The estimator only sees the gap between consecutive clicks, so testing it
    on a gap series isolates the maths from the loop's deadline handling.
    """
    clicker = Clicker(StubMouse(FakeClock(), 0.0), StubApp())
    clock = FakeClock()
    clicker._record_click(clock.now)
    readings = []
    for gap in gaps:
        clock.advance(gap)
        clicker._record_click(clock.now)
        readings.append(clicker.measured_cps)
    return readings


class MeasuredRateTests(unittest.TestCase):
    def test_reports_the_true_rate_on_a_steady_stream(self):
        for cps in (5, 20, 70, 200):
            with self.subTest(cps=cps):
                readings = run_measured(cps, 0.0, 60)
                self.assertAlmostEqual(readings[-1], cps, delta=0.5)

    def test_reports_zero_before_the_first_click_and_after_a_stop(self):
        clock = FakeClock()
        clicker = Clicker(StubMouse(clock, 0.0), StubApp())
        self.assertEqual(clicker.measured_cps, 0.0)
        readings = run_measured(20, 0.0, 10)
        self.assertGreater(readings[-1], 0.0)
        clicker.stop()
        self.assertEqual(clicker.measured_cps, 0.0)

    def test_a_stall_shows_up_within_a_few_clicks(self):
        readings = run_measured(20, 0.0, 60, stall_after=20, stall_for=0.5)
        # The click that spans the stall, then the two after it.
        self.assertLess(readings[20], 14.0)
        self.assertLess(readings[22], 18.0)
        # And it recovers to the true rate once the stall is out of the average.
        self.assertAlmostEqual(readings[-1], 20.0, delta=0.5)

    def test_jitter_does_not_inflate_the_reported_rate(self):
        import random
        for cps, jitter in ((70, 0.0005), (200, 0.0005)):
            with self.subTest(cps=cps):
                rng = random.Random(11)
                period = 1.0 / cps
                gaps = [period + rng.uniform(-jitter, jitter) for _ in range(600)]
                readings = feed_intervals(gaps)
                self.assertAlmostEqual(
                    sum(readings[-100:]) / 100.0, cps, delta=cps * 0.05
                )
                # A single short gap may read high, but the average must not
                # sit above the true rate.
                self.assertLessEqual(
                    sum(readings[-100:]) / 100.0, cps * 1.05
                )

    def test_restart_does_not_carry_the_previous_rate(self):
        first = run_measured(20, 0.0, 30)
        self.assertAlmostEqual(first[-1], 20.0, delta=0.5)
        # A second run at a different rate must not be pulled by the first.
        second = run_measured(200, 0.0, 30)
        self.assertAlmostEqual(second[-1], 200.0, delta=1.0)


class TumblingCountDiscriminatorTests(unittest.TestCase):
    """The measured rate must beat a naive count over the same second."""

    def test_reported_rate_corrects_a_warmup_undercount(self):
        times = run_loop(20, 0.0, 40)
        # The first click waits one full period, so in the first second
        # [0, 1.0) a tumbling count sees the clicks at 0.05 .. 0.95 only.
        tumbling = sum(1 for t in times if 0.0 <= t < 1.0)
        self.assertEqual(tumbling, 19)
        # The delivered rate over that same stretch is 20, and the estimator
        # says so on the very first click rather than on a window boundary.
        readings = feed_intervals([0.05] * 19)
        self.assertAlmostEqual(readings[0], 20.0, delta=0.5)


if __name__ == "__main__":
    unittest.main()
