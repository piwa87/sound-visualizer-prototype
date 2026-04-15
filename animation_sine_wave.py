"""Animated travelling sine wave.

Renders a looping Matplotlib animation of a sine wave propagating along the
x-axis.  Useful as a conceptual illustration of how a periodic waveform
changes over time before it is digitised.

Usage::

    python animation_sine_wave.py
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D

# ── Figure & animation parameters ──────────────────────────────────────────
FIGURE_SIZE: tuple[float, float] = (7.50, 3.50)
X_RANGE: tuple[float, float] = (0.0, 2.0)
Y_RANGE: tuple[float, float] = (-2.0, 2.0)
NUM_POINTS: int = 1000
FRAMES: int = 200
INTERVAL_MS: int = 20
PHASE_STEP: float = 0.01


def init_line(line: Line2D) -> tuple[Line2D]:
    """Initialise the animated line with empty data.

    Args:
        line: The Matplotlib line artist to reset.

    Returns:
        A one-element tuple containing *line*, as required by
        :class:`~matplotlib.animation.FuncAnimation`.
    """
    line.set_data([], [])
    return (line,)


def animate_frame(frame: int, line: Line2D) -> tuple[Line2D]:
    """Update the line for a single animation frame.

    The sine wave travels to the right by shifting its phase on every frame.

    Args:
        frame: The current frame index (0-based).
        line: The Matplotlib line artist to update.

    Returns:
        A one-element tuple containing the updated *line*.
    """
    x = np.linspace(X_RANGE[0], X_RANGE[1], NUM_POINTS)
    y = np.sin(2 * np.pi * (x - PHASE_STEP * frame))
    line.set_data(x, y)
    return (line,)


def main() -> None:
    """Set up the figure and run the sine-wave animation."""
    plt.rcParams["figure.figsize"] = FIGURE_SIZE
    plt.rcParams["figure.autolayout"] = True

    fig, ax = plt.subplots()
    ax.set_xlim(*X_RANGE)
    ax.set_ylim(*Y_RANGE)
    ax.set_title("Travelling Sine Wave")
    ax.set_xlabel("x")
    ax.set_ylabel("Amplitude")

    (line,) = ax.plot([], [], lw=2)

    # Keep a reference to the animation object to prevent garbage-collection
    # before plt.show() is reached.
    _animation = FuncAnimation(
        fig,
        lambda frame: animate_frame(frame, line),
        init_func=lambda: init_line(line),
        frames=FRAMES,
        interval=INTERVAL_MS,
        blit=True,
    )

    plt.show()


if __name__ == "__main__":
    main()
