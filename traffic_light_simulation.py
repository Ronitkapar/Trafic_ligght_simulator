"""Software-only Raspberry Pi traffic-light controller simulation using Tkinter."""

from __future__ import annotations

from collections.abc import Sequence
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk
from typing import NamedTuple


# Example timings. Change these values to match the required demonstration.
RED_SECONDS: int = 5
GREEN_SECONDS: int = 5
YELLOW_SECONDS: int = 2


class TrafficPhase(NamedTuple):
    """Immutable definition of a single traffic-light signal phase."""

    signal: str
    message: str
    duration: int


def validate_duration(name: str, value: object) -> int:
    """Validate that a signal duration is a positive integer.

    Args:
        name: Configuration constant name for clear error reporting.
        value: Candidate duration value.

    Returns:
        Validated positive integer duration in seconds.

    Raises:
        ValueError: If ``value`` is a boolean, non-integer, or ``<= 0``.
    """
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(
            f"{name} must be an integer greater than zero; got {value!r}."
        )
    return value


def build_phases(
    red_seconds: int | None = None,
    green_seconds: int | None = None,
    yellow_seconds: int | None = None,
) -> tuple[TrafficPhase, ...]:
    """Build and validate the ordered repeating traffic-light phase cycle.

    Defaults ``None`` arguments to the module-level ``RED_SECONDS``,
    ``GREEN_SECONDS``, and ``YELLOW_SECONDS`` constants at call time.

    Args:
        red_seconds: Optional override for the RED signal duration in seconds.
        green_seconds: Optional override for the GREEN signal duration in seconds.
        yellow_seconds: Optional override for the YELLOW signal duration in seconds.

    Returns:
        Ordered tuple of ``(RED, GREEN, YELLOW)`` ``TrafficPhase`` entries.

    Raises:
        ValueError: If any phase duration is not a positive integer.
    """
    red = validate_duration(
        "RED_SECONDS", RED_SECONDS if red_seconds is None else red_seconds
    )
    green = validate_duration(
        "GREEN_SECONDS", GREEN_SECONDS if green_seconds is None else green_seconds
    )
    yellow = validate_duration(
        "YELLOW_SECONDS", YELLOW_SECONDS if yellow_seconds is None else yellow_seconds
    )
    return (
        TrafficPhase("RED", "STOP", red),
        TrafficPhase("GREEN", "GO", green),
        TrafficPhase("YELLOW", "GET READY", yellow),
    )


def interpolate_hex_color(start_hex: str, end_hex: str, progress: float) -> str:
    """Linearly interpolate between two 6-digit RGB hex color strings.

    Args:
        start_hex: Starting color in ``#RRGGBB`` format.
        end_hex: Ending color in ``#RRGGBB`` format.
        progress: Interpolation factor clamped to ``[0.0, 1.0]``.

    Returns:
        Interpolated color formatted as lowercase ``#rrggbb``.
    """
    clamped = max(0.0, min(1.0, progress))
    start_clean = start_hex.lstrip("#")
    end_clean = end_hex.lstrip("#")
    channels: list[int] = []
    for offset in (0, 2, 4):
        start_ch = int(start_clean[offset : offset + 2], 16)
        end_ch = int(end_clean[offset : offset + 2], 16)
        channels.append(round(start_ch + (end_ch - start_ch) * clamped))
    return f"#{channels[0]:02x}{channels[1]:02x}{channels[2]:02x}"


def select_ui_font(available_families: Sequence[str]) -> str:
    """Select the cleanest available cross-platform UI sans-serif font family.

    Args:
        available_families: Font family names reported by Tkinter.

    Returns:
        Highest-priority matching family name, or ``"TkDefaultFont"`` as fallback.
    """
    preferred = (
        "Adwaita Sans",
        "Inter",
        "Segoe UI",
        "SF Pro Text",
        "Noto Sans",
        "Liberation Sans",
        "DejaVu Sans",
        "Helvetica",
    )
    available_set = set(available_families)
    for candidate in preferred:
        if candidate in available_set:
            return candidate
    return "TkDefaultFont"


class TrafficLightSimulation:
    """Display and run a timed, software-only traffic-light simulation."""

    PHASES: tuple[TrafficPhase, ...] = build_phases(
        RED_SECONDS, GREEN_SECONDS, YELLOW_SECONDS
    )
    LIGHT_ORDER: tuple[str, str, str] = ("RED", "YELLOW", "GREEN")
    TICK_INTERVAL_MS: int = 1000
    HALO_ANIM_STEPS: int = 6
    HALO_ANIM_STEP_MS: int = 35
    PROGRESS_WIDTH: int = 220

    # Daylight transit signal bench palette.
    SURFACE_BG: str = "#F3F5F7"
    CARD_BG: str = "#FFFFFF"
    CARD_BORDER: str = "#D7DEE6"
    HOUSING_FILL: str = "#1F242B"
    HOUSING_OUTLINE: str = "#13171C"
    HOUSING_INNER: str = "#2A313B"
    BEZEL_FILL: str = "#12161B"
    INK_PRIMARY: str = "#141921"
    INK_SECONDARY: str = "#526071"
    TRACK_BG: str = "#DCE3EC"

    COLORS: dict[str, tuple[str, str]] = {
        "RED": ("#E52521", "#3B1E20"),
        "YELLOW": ("#F2B705", "#3D3418"),
        "GREEN": ("#16A34A", "#193524"),
    }
    HALO_COLORS: dict[str, tuple[str, str]] = {
        "RED": ("#FFB4B0", "#F48A86"),
        "YELLOW": ("#FFF0A6", "#F7D362"),
        "GREEN": ("#A7F3C4", "#5AD48A"),
    }
    SPECULAR_COLORS: dict[str, str] = {
        "RED": "#FF8F8C",
        "YELLOW": "#FFF0A0",
        "GREEN": "#8EF5B2",
    }
    TEXT_COLORS: dict[str, str] = {
        "RED": "#B41E1B",
        "GREEN": "#137A39",
        "YELLOW": "#946800",
    }
    STATE_BADGE_STYLES: dict[str, tuple[str, str]] = {
        "Ready": ("#E8EEF5", "#3B4A5E"),
        "Running": ("#DCFCE7", "#14532D"),
        "Paused": ("#FEF3C7", "#92400E"),
    }

    def __init__(
        self,
        root: tk.Tk,
        *,
        red_seconds: int | None = None,
        green_seconds: int | None = None,
        yellow_seconds: int | None = None,
    ) -> None:
        """Initialize the traffic-light simulation window and state.

        Args:
            root: Main Tkinter root window.
            red_seconds: Optional duration override for the RED phase.
            green_seconds: Optional duration override for the GREEN phase.
            yellow_seconds: Optional duration override for the YELLOW phase.

        Raises:
            ValueError: If any configured signal duration is not a positive integer.
        """
        self.phases: tuple[TrafficPhase, ...] = build_phases(
            red_seconds, green_seconds, yellow_seconds
        )
        self.PHASES = self.phases

        self.root = root
        self.root.title("Raspberry Pi Traffic Light Controller | Simulation")
        self.root.geometry("450x710")
        self.root.minsize(400, 650)
        self.root.configure(bg=self.SURFACE_BG)

        self.phase_index: int = 0
        self.seconds_left: int = self.phases[0].duration
        self.running: bool = False
        self.after_id: str | None = None
        self._anim_after_id: str | None = None
        self._has_started: bool = False

        try:
            available_fonts = tkfont.families(self.root)
        except tk.TclError:
            available_fonts = ()
        self.ui_font: str = select_ui_font(available_fonts)

        self._build_interface()
        self._render(animate_halo=False)
        self._update_controls()

        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.bind("<Destroy>", self._on_destroy)

    def _widget_alive(self) -> bool:
        """Return whether the root window still exists in Tcl/Tk."""
        try:
            return bool(self.root.winfo_exists())
        except tk.TclError:
            return False

    def _create_rounded_rectangle(
        self,
        canvas: tk.Canvas,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        radius: int,
        **kwargs: object,
    ) -> int:
        """Draw a rounded rectangle polygon on ``canvas``."""
        points = (
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        )
        return canvas.create_polygon(points, smooth=True, splinesteps=24, **kwargs)  # type: ignore[arg-type]

    def _build_interface(self) -> None:
        """Construct the signal housing, readouts, control buttons, and spec card."""
        self._configure_styles()

        container = tk.Frame(self.root, bg=self.SURFACE_BG)
        container.pack(expand=True)

        header = tk.Frame(container, bg=self.SURFACE_BG)
        header.pack(pady=(16, 10))

        tk.Label(
            header,
            text="Traffic Light Controller",
            font=(self.ui_font, 16, "bold"),
            bg=self.SURFACE_BG,
            fg=self.INK_PRIMARY,
        ).pack()

        tk.Label(
            header,
            text="Raspberry Pi software simulation",
            font=(self.ui_font, 9),
            bg=self.SURFACE_BG,
            fg=self.INK_SECONDARY,
        ).pack(pady=(2, 0))

        self.canvas = tk.Canvas(
            container,
            width=220,
            height=344,
            bg=self.SURFACE_BG,
            highlightthickness=0,
        )
        self.canvas.pack()

        # Mounting cap and base post accents around the cast-aluminum housing.
        self._create_rounded_rectangle(
            self.canvas,
            88,
            4,
            132,
            18,
            radius=6,
            fill="#2E3642",
            outline=self.HOUSING_OUTLINE,
            width=2,
        )
        self.canvas.create_rectangle(
            94,
            326,
            126,
            340,
            fill="#2E3642",
            outline=self.HOUSING_OUTLINE,
            width=2,
        )

        # Outer signal housing and recessed inner bezel panel.
        self._create_rounded_rectangle(
            self.canvas,
            38,
            12,
            182,
            330,
            radius=28,
            fill=self.HOUSING_FILL,
            outline=self.HOUSING_OUTLINE,
            width=3,
        )
        self._create_rounded_rectangle(
            self.canvas,
            48,
            22,
            172,
            320,
            radius=20,
            fill=self.HOUSING_FILL,
            outline=self.HOUSING_INNER,
            width=1,
        )

        self.halo_ids: dict[str, int] = {}
        self.light_ids: dict[str, int] = {}
        self.specular_ids: dict[str, int] = {}

        light_positions: dict[str, tuple[int, int]] = {
            "RED": (110, 72),
            "YELLOW": (110, 171),
            "GREEN": (110, 270),
        }
        for name in self.LIGHT_ORDER:
            cx, cy = light_positions[name]
            # Recessed socket bezel.
            self.canvas.create_oval(
                cx - 42,
                cy - 42,
                cx + 42,
                cy + 42,
                fill=self.BEZEL_FILL,
                outline="#0C0F13",
                width=2,
            )
            # Active-only subtle outer halo ring.
            self.halo_ids[name] = self.canvas.create_oval(
                cx - 40,
                cy - 40,
                cx + 40,
                cy + 40,
                fill="",
                outline=self.HALO_COLORS[name][1],
                width=3,
                state="hidden",
            )
            # Primary circular signal lens.
            self.light_ids[name] = self.canvas.create_oval(
                cx - 35,
                cy - 35,
                cx + 35,
                cy + 35,
                fill=self.COLORS[name][1],
                outline="#0B0E12",
                width=2,
            )
            # Active-only specular crescent near top-left of lens.
            self.specular_ids[name] = self.canvas.create_arc(
                cx - 25,
                cy - 25,
                cx + 25,
                cy + 25,
                start=112,
                extent=52,
                style=tk.ARC,
                outline=self.SPECULAR_COLORS[name],
                width=3,
                state="hidden",
            )

        readout = tk.Frame(container, bg=self.SURFACE_BG)
        readout.pack(pady=(10, 10))

        self.status_label = tk.Label(
            readout,
            text="RED – STOP",
            font=(self.ui_font, 18, "bold"),
            bg=self.SURFACE_BG,
            fg=self.TEXT_COLORS["RED"],
        )
        self.status_label.pack()

        self.timer_label = tk.Label(
            readout,
            text="5 seconds remaining",
            font=(self.ui_font, 11),
            bg=self.SURFACE_BG,
            fg=self.INK_PRIMARY,
        )
        self.timer_label.pack(pady=(2, 8))

        self.progress_canvas = tk.Canvas(
            readout,
            width=self.PROGRESS_WIDTH,
            height=6,
            bg=self.TRACK_BG,
            highlightthickness=0,
        )
        self.progress_canvas.pack()
        self.progress_fill_id: int = self.progress_canvas.create_rectangle(
            0,
            0,
            self.PROGRESS_WIDTH,
            6,
            fill=self.COLORS["RED"][0],
            outline="",
        )

        self.state_label = tk.Label(
            readout,
            text="Ready",
            font=(self.ui_font, 9, "bold"),
            padx=12,
            pady=3,
            bg=self.STATE_BADGE_STYLES["Ready"][0],
            fg=self.STATE_BADGE_STYLES["Ready"][1],
        )
        self.state_label.pack(pady=(10, 0))

        controls = tk.Frame(container, bg=self.SURFACE_BG)
        controls.pack(pady=(2, 12))

        self.start_button = ttk.Button(
            controls,
            text="Start",
            style="Primary.TButton",
            command=self.start,
            width=9,
        )
        self.start_button.grid(row=0, column=0, padx=6)

        self.pause_button = ttk.Button(
            controls,
            text="Pause",
            style="Secondary.TButton",
            command=self.pause,
            width=9,
        )
        self.pause_button.grid(row=0, column=1, padx=6)

        self.reset_button = ttk.Button(
            controls,
            text="Reset",
            style="Secondary.TButton",
            command=self.reset,
            width=9,
        )
        self.reset_button.grid(row=0, column=2, padx=6)

        spec_card = tk.Frame(
            container,
            bg=self.CARD_BG,
            highlightbackground=self.CARD_BORDER,
            highlightthickness=1,
            padx=20,
            pady=10,
        )
        spec_card.pack(padx=24, pady=(0, 14))

        red_phase, green_phase, yellow_phase = self.phases
        timing_text = (
            f"Configured durations: Red {red_phase.duration}s  |  "
            f"Green {green_phase.duration}s  |  "
            f"Yellow {yellow_phase.duration}s"
        )
        self.timing_label = tk.Label(
            spec_card,
            text=timing_text,
            font=(self.ui_font, 9),
            bg=self.CARD_BG,
            fg=self.INK_SECONDARY,
        )
        self.timing_label.pack()

        self.sequence_label = tk.Label(
            spec_card,
            text="Sequence: RED → GREEN → YELLOW → RED",
            font=(self.ui_font, 9, "bold"),
            bg=self.CARD_BG,
            fg=self.INK_PRIMARY,
        )
        self.sequence_label.pack(pady=(4, 0))

    def _configure_styles(self) -> None:
        """Configure ttk button styles with crisp enabled and disabled contrast."""
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Primary.TButton",
            font=(self.ui_font, 10, "bold"),
            padding=(12, 7),
            background="#1D4ED8",
            foreground="#FFFFFF",
            bordercolor="#1E40AF",
            focuscolor="#93C5FD",
        )
        style.map(
            "Primary.TButton",
            background=[
                ("disabled", "#CBD5E1"),
                ("pressed", "#1E3A8A"),
                ("active", "#1E40AF"),
            ],
            foreground=[("disabled", "#64748B")],
            bordercolor=[("disabled", "#CBD5E1")],
        )

        style.configure(
            "Secondary.TButton",
            font=(self.ui_font, 10, "bold"),
            padding=(12, 7),
            background="#FFFFFF",
            foreground=self.INK_PRIMARY,
            bordercolor="#C3CDD9",
            focuscolor="#93C5FD",
        )
        style.map(
            "Secondary.TButton",
            background=[
                ("disabled", "#E5E9F0"),
                ("pressed", "#E2E8F0"),
                ("active", "#F8FAFC"),
            ],
            foreground=[("disabled", "#8A96A6")],
            bordercolor=[("disabled", "#D5DCE5")],
        )

    def _update_controls(self) -> None:
        """Synchronize button states and the simulation status badge."""
        if not self._widget_alive():
            return
        try:
            if self.running:
                state_name = "Running"
                self.start_button.configure(state="disabled")
                self.pause_button.configure(state="normal")
            elif self._has_started:
                state_name = "Paused"
                self.start_button.configure(state="normal")
                self.pause_button.configure(state="disabled")
            else:
                state_name = "Ready"
                self.start_button.configure(state="normal")
                self.pause_button.configure(state="disabled")

            badge_bg, badge_fg = self.STATE_BADGE_STYLES[state_name]
            self.state_label.configure(text=state_name, bg=badge_bg, fg=badge_fg)
        except tk.TclError:
            return

    def _render(self, *, animate_halo: bool = False) -> None:
        """Update canvas lenses, status readout, countdown text, and progress bar."""
        if not self._widget_alive():
            return

        self._cancel_animation()
        phase = self.phases[self.phase_index]

        try:
            for light in self.LIGHT_ORDER:
                active_color, inactive_color = self.COLORS[light]
                is_active = light == phase.signal
                self.canvas.itemconfigure(
                    self.light_ids[light],
                    fill=active_color if is_active else inactive_color,
                )
                self.canvas.itemconfigure(
                    self.halo_ids[light],
                    state="normal" if is_active else "hidden",
                    outline=self.HALO_COLORS[light][1],
                    width=3,
                )
                self.canvas.itemconfigure(
                    self.specular_ids[light],
                    state="normal" if is_active else "hidden",
                )

            self.status_label.configure(
                text=f"{phase.signal} – {phase.message}",
                fg=self.TEXT_COLORS[phase.signal],
            )
            unit = "second" if self.seconds_left == 1 else "seconds"
            self.timer_label.configure(text=f"{self.seconds_left} {unit} remaining")

            fill_width = max(
                0,
                round(self.PROGRESS_WIDTH * self.seconds_left / phase.duration),
            )
            self.progress_canvas.coords(self.progress_fill_id, 0, 0, fill_width, 6)
            self.progress_canvas.itemconfigure(
                self.progress_fill_id,
                fill=self.COLORS[phase.signal][0],
            )
        except tk.TclError:
            return

        if animate_halo and self.running:
            self._animate_halo(phase.signal, step=0)

    def _animate_halo(self, signal: str, step: int) -> None:
        """Run a brief ease-out halo settle strictly on the single active light."""
        self._anim_after_id = None
        if not self.running or not self._widget_alive():
            return
        if self.phases[self.phase_index].signal != signal:
            return

        progress = step / self.HALO_ANIM_STEPS
        eased = 1.0 - (1.0 - progress) ** 2
        burst_hex, steady_hex = self.HALO_COLORS[signal]
        halo_color = interpolate_hex_color(burst_hex, steady_hex, eased)
        halo_width = 6.0 - 3.0 * eased

        try:
            self.canvas.itemconfigure(
                self.halo_ids[signal],
                outline=halo_color,
                width=halo_width,
                state="normal",
            )
        except tk.TclError:
            return

        if step < self.HALO_ANIM_STEPS:
            try:
                self._anim_after_id = self.root.after(
                    self.HALO_ANIM_STEP_MS,
                    lambda: self._animate_halo(signal, step + 1),
                )
            except tk.TclError:
                self._anim_after_id = None

    def start(self) -> None:
        """Start the traffic-light sequence or resume from a paused state."""
        if self.running or not self._widget_alive():
            return
        self.running = True
        self._has_started = True
        self._update_controls()
        self._schedule_tick()

    def pause(self) -> None:
        """Pause countdown updates while preserving the active signal and time."""
        self.running = False
        self._cancel_tick()
        self._cancel_animation()
        self._update_controls()

    def reset(self) -> None:
        """Stop the simulation and restore the initial full-duration RED state."""
        self.running = False
        self._has_started = False
        self._cancel_tick()
        self._cancel_animation()
        self.phase_index = 0
        self.seconds_left = self.phases[0].duration
        self._render(animate_halo=False)
        self._update_controls()

    def _schedule_tick(self) -> None:
        """Schedule the next one-second simulation tick without duplicates."""
        self._cancel_tick()
        if not self.running or not self._widget_alive():
            return
        try:
            self.after_id = self.root.after(self.TICK_INTERVAL_MS, self._tick)
        except tk.TclError:
            self.after_id = None

    def _tick(self) -> None:
        """Advance the countdown by one second and transition phases on zero."""
        self._cancel_tick()
        if not self.running or not self._widget_alive():
            return

        phase_changed = False
        self.seconds_left -= 1
        if self.seconds_left <= 0:
            self.phase_index = (self.phase_index + 1) % len(self.phases)
            self.seconds_left = self.phases[self.phase_index].duration
            phase_changed = True

        self._render(animate_halo=phase_changed)
        self._schedule_tick()

    def _cancel_tick(self) -> None:
        """Cancel any pending one-second simulation timer callback."""
        if self.after_id is not None:
            try:
                self.root.after_cancel(self.after_id)
            except tk.TclError:
                pass
            self.after_id = None

    def _cancel_animation(self) -> None:
        """Cancel any pending halo transition animation callback."""
        if self._anim_after_id is not None:
            try:
                self.root.after_cancel(self._anim_after_id)
            except tk.TclError:
                pass
            self._anim_after_id = None

    def _on_destroy(self, event: tk.Event[tk.Misc]) -> None:
        """Ensure pending callbacks are stopped if the root widget is destroyed."""
        if event.widget is self.root:
            self.running = False
            self._cancel_tick()
            self._cancel_animation()

    def _close(self) -> None:
        """Cancel pending callbacks and close the application window cleanly."""
        self.running = False
        self._cancel_tick()
        self._cancel_animation()
        if self._widget_alive():
            try:
                self.root.destroy()
            except tk.TclError:
                pass


def main() -> None:
    """Validate timings, launch the simulation window, and enter the GUI loop."""
    build_phases(RED_SECONDS, GREEN_SECONDS, YELLOW_SECONDS)
    root = tk.Tk()
    TrafficLightSimulation(root)
    root.mainloop()


if __name__ == "__main__":
    main()
