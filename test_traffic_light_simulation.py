"""Automated tests for the software-only Raspberry Pi traffic-light simulation."""

from __future__ import annotations

import ast
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import sys
import time
import tkinter as tk
import unittest
from unittest.mock import patch

import traffic_light_simulation as sim_mod


PROJECT_DIR = Path(__file__).resolve().parent
SIMULATION_PATH = PROJECT_DIR / "traffic_light_simulation.py"


@contextmanager
def patched_module_timings(
    red: object,
    green: object,
    yellow: object,
) -> Iterator[None]:
    """Temporarily override module-level timing constants and restore them."""
    original = (
        sim_mod.RED_SECONDS,
        sim_mod.GREEN_SECONDS,
        sim_mod.YELLOW_SECONDS,
    )
    sim_mod.RED_SECONDS = red  # type: ignore[assignment]
    sim_mod.GREEN_SECONDS = green  # type: ignore[assignment]
    sim_mod.YELLOW_SECONDS = yellow  # type: ignore[assignment]
    try:
        yield
    finally:
        (
            sim_mod.RED_SECONDS,
            sim_mod.GREEN_SECONDS,
            sim_mod.YELLOW_SECONDS,
        ) = original


def pending_after_ids(root: tk.Tk) -> set[str]:
    """Return the set of currently scheduled Tcl ``after`` IDs for ``root``."""
    return set(root.tk.splitlist(root.tk.call("after", "info")))


class TrafficLightTestCase(unittest.TestCase):
    """Base test case providing an isolated, withdrawn Tkinter root."""

    def setUp(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        self._root_destroyed = False

    def tearDown(self) -> None:
        if not self._root_destroyed:
            try:
                if self.root.winfo_exists():
                    self.root.destroy()
            except tk.TclError:
                pass

    def _assert_single_active_light(
        self,
        sim: sim_mod.TrafficLightSimulation,
        expected_signal: str,
    ) -> None:
        """Verify strictly one lens is illuminated and only its halo is shown."""
        for light in ("RED", "YELLOW", "GREEN"):
            active_color, inactive_color = sim.COLORS[light]
            expected_fill = active_color if light == expected_signal else inactive_color
            actual_fill = sim.canvas.itemcget(sim.light_ids[light], "fill")
            self.assertEqual(
                actual_fill,
                expected_fill,
                f"Expected {light} fill {expected_fill!r}, got {actual_fill!r}",
            )

            expected_state = "normal" if light == expected_signal else "hidden"
            actual_halo_state = sim.canvas.itemcget(sim.halo_ids[light], "state")
            self.assertEqual(
                actual_halo_state,
                expected_state,
                f"Expected {light} halo state {expected_state!r}, got {actual_halo_state!r}",
            )


class TestTimingConfigurationAndHelpers(TrafficLightTestCase):
    """Verify timing defaults, validation, dynamic config, and pure helpers."""

    def test_default_timing_constants_and_build_phases(self) -> None:
        self.assertEqual(sim_mod.RED_SECONDS, 5)
        self.assertEqual(sim_mod.GREEN_SECONDS, 5)
        self.assertEqual(sim_mod.YELLOW_SECONDS, 2)

        phases = sim_mod.build_phases()
        self.assertEqual(
            phases,
            (
                sim_mod.TrafficPhase("RED", "STOP", 5),
                sim_mod.TrafficPhase("GREEN", "GO", 5),
                sim_mod.TrafficPhase("YELLOW", "GET READY", 2),
            ),
        )

    def test_invalid_durations_rejected_by_build_phases_and_simulation(self) -> None:
        invalid_arg_values: list[object] = [0, -1, True, False, 2.5, "5"]
        for bad in invalid_arg_values:
            cases = [
                (bad, 5, 2),
                (5, bad, 2),
                (5, 5, bad),
            ]
            for red, green, yellow in cases:
                with self.subTest(mode="arg", red=red, green=green, yellow=yellow):
                    with self.assertRaises(ValueError):
                        sim_mod.build_phases(red, green, yellow)  # type: ignore[arg-type]
                    with self.assertRaises(ValueError):
                        sim_mod.TrafficLightSimulation(
                            self.root,
                            red_seconds=red,  # type: ignore[arg-type]
                            green_seconds=green,  # type: ignore[arg-type]
                            yellow_seconds=yellow,  # type: ignore[arg-type]
                        )

        invalid_module_values: list[object] = [0, -1, True, False, 2.5, "5", None]
        for bad in invalid_module_values:
            cases = [
                (bad, 5, 2),
                (5, bad, 2),
                (5, 5, bad),
            ]
            for red, green, yellow in cases:
                with self.subTest(mode="module", red=red, green=green, yellow=yellow):
                    with patched_module_timings(red, green, yellow):
                        with self.assertRaises(ValueError):
                            sim_mod.build_phases()
                        with self.assertRaises(ValueError):
                            sim_mod.TrafficLightSimulation(self.root)

    def test_main_rejects_invalid_module_timings_before_creating_tk(self) -> None:
        invalid_values: list[object] = [0, -1, True, False, 2.5, "5", None]
        for bad in invalid_values:
            with self.subTest(bad=bad):
                with (
                    patched_module_timings(bad, 5, 2),
                    patch.object(
                        sim_mod.tk,
                        "Tk",
                        side_effect=AssertionError(
                            "tk.Tk() must not be created for invalid timing config"
                        ),
                    ),
                ):
                    with self.assertRaises(ValueError):
                        sim_mod.main()

    def test_custom_durations_via_arguments_and_module_constants(self) -> None:
        sim = sim_mod.TrafficLightSimulation(
            self.root,
            red_seconds=3,
            green_seconds=2,
            yellow_seconds=1,
        )
        self.assertEqual(
            sim.phases,
            (
                sim_mod.TrafficPhase("RED", "STOP", 3),
                sim_mod.TrafficPhase("GREEN", "GO", 2),
                sim_mod.TrafficPhase("YELLOW", "GET READY", 1),
            ),
        )
        self.assertEqual(sim.seconds_left, 3)
        self.assertEqual(sim.timer_label.cget("text"), "3 seconds remaining")
        timing_text = sim.timing_label.cget("text")
        self.assertIn("Red 3s", timing_text)
        self.assertIn("Green 2s", timing_text)
        self.assertIn("Yellow 1s", timing_text)
        sim._close()
        self._root_destroyed = True

        fresh_root = tk.Tk()
        fresh_root.withdraw()
        self.addCleanup(
            lambda: fresh_root.destroy() if fresh_root.winfo_exists() else None
        )
        with patched_module_timings(7, 4, 2):
            mod_sim = sim_mod.TrafficLightSimulation(fresh_root)
        self.assertEqual(mod_sim.seconds_left, 7)
        self.assertIn("Red 7s", mod_sim.timing_label.cget("text"))
        self.assertIn("Green 4s", mod_sim.timing_label.cget("text"))
        self.assertIn("Yellow 2s", mod_sim.timing_label.cget("text"))

    def test_interpolate_hex_color_clamping_and_midpoint(self) -> None:
        self.assertEqual(
            sim_mod.interpolate_hex_color("#000000", "#ffffff", 0.0),
            "#000000",
        )
        self.assertEqual(
            sim_mod.interpolate_hex_color("#000000", "#ffffff", 1.0),
            "#ffffff",
        )
        self.assertEqual(
            sim_mod.interpolate_hex_color("#000000", "#ffffff", 0.5),
            "#808080",
        )
        self.assertEqual(
            sim_mod.interpolate_hex_color("#123456", "#abcdef", -0.5),
            "#123456",
        )
        self.assertEqual(
            sim_mod.interpolate_hex_color("#123456", "#abcdef", 1.5),
            "#abcdef",
        )

    def test_select_ui_font_priority_and_fallback(self) -> None:
        self.assertEqual(
            sim_mod.select_ui_font(["DejaVu Sans", "Inter", "Segoe UI"]),
            "Inter",
        )
        self.assertEqual(
            sim_mod.select_ui_font(["Courier", "Adwaita Sans", "Inter"]),
            "Adwaita Sans",
        )
        self.assertEqual(
            sim_mod.select_ui_font(["Unknown Font"]),
            "TkDefaultFont",
        )
        self.assertEqual(sim_mod.select_ui_font([]), "TkDefaultFont")


class TestInitialStateAndCycleProgression(TrafficLightTestCase):
    """Verify initial UI state, single-light invariant, and 24-tick cycle."""

    def test_initial_state_and_ui_elements(self) -> None:
        sim = sim_mod.TrafficLightSimulation(self.root)

        self.assertEqual(sim.phase_index, 0)
        self.assertEqual(sim.seconds_left, 5)
        self.assertFalse(sim.running)
        self.assertIsNone(sim.after_id)

        self.assertEqual(sim.status_label.cget("text"), "RED – STOP")
        self.assertEqual(sim.timer_label.cget("text"), "5 seconds remaining")
        self.assertEqual(sim.state_label.cget("text"), "Ready")

        self.assertTrue(sim.start_button.instate(["!disabled"]))
        self.assertTrue(sim.pause_button.instate(["disabled"]))
        self.assertTrue(sim.reset_button.instate(["!disabled"]))

        self._assert_single_active_light(sim, "RED")

        timing_text = sim.timing_label.cget("text")
        self.assertIn("Red 5s", timing_text)
        self.assertIn("Green 5s", timing_text)
        self.assertIn("Yellow 2s", timing_text)
        self.assertEqual(
            sim.sequence_label.cget("text"),
            "Sequence: RED → GREEN → YELLOW → RED",
        )

    def test_full_repeating_cycle_for_two_complete_cycles(self) -> None:
        sim = sim_mod.TrafficLightSimulation(self.root)
        sim.start()

        expected_cycle: list[tuple[str, str, int]] = [
            ("RED", "STOP", 4),
            ("RED", "STOP", 3),
            ("RED", "STOP", 2),
            ("RED", "STOP", 1),
            ("GREEN", "GO", 5),
            ("GREEN", "GO", 4),
            ("GREEN", "GO", 3),
            ("GREEN", "GO", 2),
            ("GREEN", "GO", 1),
            ("YELLOW", "GET READY", 2),
            ("YELLOW", "GET READY", 1),
            ("RED", "STOP", 5),
        ]
        expected_24_ticks = expected_cycle + expected_cycle

        for tick_num, (exp_sig, exp_msg, exp_sec) in enumerate(
            expected_24_ticks, start=1
        ):
            sim._tick()
            with self.subTest(tick=tick_num, expected=(exp_sig, exp_msg, exp_sec)):
                phase = sim.phases[sim.phase_index]
                self.assertEqual(phase.signal, exp_sig)
                self.assertEqual(phase.message, exp_msg)
                self.assertEqual(sim.seconds_left, exp_sec)
                self.assertEqual(
                    sim.status_label.cget("text"), f"{exp_sig} – {exp_msg}"
                )
                expected_unit = "second" if exp_sec == 1 else "seconds"
                self.assertEqual(
                    sim.timer_label.cget("text"),
                    f"{exp_sec} {expected_unit} remaining",
                )
                self._assert_single_active_light(sim, exp_sig)


class TestControlsAndLifecycle(TrafficLightTestCase):
    """Verify Start, Pause, Reset, callback cancellation, and close cleanup."""

    def test_start_prevents_duplicate_callbacks_and_pause_preserves_state(self) -> None:
        sim = sim_mod.TrafficLightSimulation(self.root)
        baseline_ids = pending_after_ids(self.root)

        sim.start()
        self.assertTrue(sim.running)
        self.assertIsNotNone(sim.after_id)
        self.assertEqual(sim.state_label.cget("text"), "Running")
        self.assertTrue(sim.start_button.instate(["disabled"]))
        self.assertTrue(sim.pause_button.instate(["!disabled"]))

        first_after_id = sim.after_id
        after_first_start = pending_after_ids(self.root) - baseline_ids
        self.assertEqual(after_first_start, {first_after_id})

        # Calling start again while running must be a no-op with no new timer.
        sim.start()
        self.assertEqual(sim.after_id, first_after_id)
        self.assertEqual(pending_after_ids(self.root) - baseline_ids, {first_after_id})

        # Advance into GREEN with 3 seconds remaining (7 ticks: 5->1 RED + 5->3 GREEN).
        for _ in range(7):
            sim._tick()
        self.assertEqual(sim.phases[sim.phase_index].signal, "GREEN")
        self.assertEqual(sim.seconds_left, 3)

        sim.pause()
        self.assertFalse(sim.running)
        self.assertIsNone(sim.after_id)
        self.assertIsNone(sim._anim_after_id)
        self.assertEqual(pending_after_ids(self.root) - baseline_ids, set())
        self.assertEqual(sim.phases[sim.phase_index].signal, "GREEN")
        self.assertEqual(sim.seconds_left, 3)
        self.assertEqual(sim.status_label.cget("text"), "GREEN – GO")
        self.assertEqual(sim.timer_label.cget("text"), "3 seconds remaining")
        self.assertEqual(sim.state_label.cget("text"), "Paused")
        self.assertTrue(sim.start_button.instate(["!disabled"]))
        self.assertTrue(sim.pause_button.instate(["disabled"]))
        self._assert_single_active_light(sim, "GREEN")

        # Stale _tick invocation while paused must not mutate state or reschedule.
        sim._tick()
        self.assertEqual(sim.seconds_left, 3)
        self.assertIsNone(sim.after_id)

        # Resuming continues cleanly from GREEN 3s -> 2s.
        sim.start()
        self.assertTrue(sim.running)
        self.assertEqual(sim.state_label.cget("text"), "Running")
        sim._tick()
        self.assertEqual(sim.phases[sim.phase_index].signal, "GREEN")
        self.assertEqual(sim.seconds_left, 2)

    def test_reset_from_running_and_from_paused_restores_initial_red(self) -> None:
        sim = sim_mod.TrafficLightSimulation(self.root)
        baseline_ids = pending_after_ids(self.root)

        # Advance into YELLOW with 1 second remaining (5 + 5 + 1 = 11 ticks).
        sim.start()
        for _ in range(11):
            sim._tick()
        self.assertEqual(sim.phases[sim.phase_index].signal, "YELLOW")
        self.assertEqual(sim.seconds_left, 1)

        # Reset while running.
        sim.reset()
        self.assertFalse(sim.running)
        self.assertIsNone(sim.after_id)
        self.assertIsNone(sim._anim_after_id)
        self.assertEqual(pending_after_ids(self.root) - baseline_ids, set())
        self.assertEqual(sim.phase_index, 0)
        self.assertEqual(sim.seconds_left, 5)
        self.assertEqual(sim.status_label.cget("text"), "RED – STOP")
        self.assertEqual(sim.timer_label.cget("text"), "5 seconds remaining")
        self.assertEqual(sim.state_label.cget("text"), "Ready")
        self.assertTrue(sim.start_button.instate(["!disabled"]))
        self.assertTrue(sim.pause_button.instate(["disabled"]))
        self._assert_single_active_light(sim, "RED")

        # Advance into GREEN 2s, pause, then reset from paused.
        sim.start()
        for _ in range(8):
            sim._tick()
        self.assertEqual(sim.phases[sim.phase_index].signal, "GREEN")
        self.assertEqual(sim.seconds_left, 2)
        sim.pause()
        sim.reset()
        self.assertFalse(sim.running)
        self.assertEqual(sim.phase_index, 0)
        self.assertEqual(sim.seconds_left, 5)
        self.assertEqual(sim.state_label.cget("text"), "Ready")
        self._assert_single_active_light(sim, "RED")

    def test_close_cleans_callbacks_and_handles_repeat_close_or_destroyed_root(self) -> None:
        sim = sim_mod.TrafficLightSimulation(self.root)
        sim.start()
        # Trigger a phase change so halo animation callback is also active.
        for _ in range(5):
            sim._tick()

        sim._close()
        self._root_destroyed = True
        self.assertFalse(sim.running)
        self.assertIsNone(sim.after_id)
        self.assertIsNone(sim._anim_after_id)

        # Repeated close, start, and tick after destruction must not raise TclError.
        sim._close()
        sim.start()
        sim._tick()
        self.assertFalse(sim.running)
        self.assertIsNone(sim.after_id)

    def test_direct_root_destroy_cancels_callbacks_via_destroy_binding(self) -> None:
        sim = sim_mod.TrafficLightSimulation(self.root)
        sim.start()
        for _ in range(5):
            sim._tick()
        self.assertIsNotNone(sim.after_id)

        self.root.destroy()
        self._root_destroyed = True
        self.assertFalse(sim.running)
        self.assertIsNone(sim.after_id)
        self.assertIsNone(sim._anim_after_id)


class TestLiveEventLoopAndLayoutCompliance(TrafficLightTestCase):
    """Verify real Tkinter after() timer, layout fit, and stdlib-only scope."""

    def test_live_tkinter_after_callback_advances_countdown(self) -> None:
        sim = sim_mod.TrafficLightSimulation(self.root)
        sim.start()
        self.assertEqual(sim.seconds_left, 5)

        # Drive real Tkinter event loop with short condition-based polling.
        deadline = time.monotonic() + 2.5
        while time.monotonic() < deadline and sim.seconds_left == 5:
            self.root.update()
            time.sleep(0.025)

        self.assertEqual(sim.seconds_left, 4)
        self.assertEqual(sim.phases[sim.phase_index].signal, "RED")
        self.assertEqual(sim.timer_label.cget("text"), "4 seconds remaining")

        sim._close()
        self._root_destroyed = True
        self.assertFalse(sim.running)
        self.assertIsNone(sim.after_id)

    def test_layout_requested_size_fits_default_window(self) -> None:
        sim = sim_mod.TrafficLightSimulation(self.root)
        self.root.update_idletasks()
        self.assertLessEqual(self.root.winfo_reqwidth(), 450)
        self.assertLessEqual(self.root.winfo_reqheight(), 710)
        sim._close()
        self._root_destroyed = True

    def test_source_uses_only_stdlib_and_never_uses_time_sleep(self) -> None:
        source = SIMULATION_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(SIMULATION_PATH))

        imported_top_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_top_modules.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_top_modules.add(node.module.split(".")[0])
            elif isinstance(node, ast.Attribute) and node.attr == "sleep":
                self.fail("traffic_light_simulation.py must not call sleep()")

        self.assertNotIn("time", imported_top_modules)
        non_stdlib = imported_top_modules - sys.stdlib_module_names
        self.assertEqual(
            non_stdlib,
            set(),
            f"Unexpected third-party imports: {sorted(non_stdlib)}",
        )


if __name__ == "__main__":
    unittest.main()
