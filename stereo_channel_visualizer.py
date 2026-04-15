"""Stereo channel sound visualizer.

Loads a stereo audio file, computes the STFT for each channel independently,
and displays two dB-scaled spectrograms (left and right) stacked vertically.

Usage::

    python stereo_channel_visualizer.py
"""

from pathlib import Path

import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
from playsound import playsound

from utils import get_menu_choice

SCRIPT_DIR = Path(__file__).parent

SOUNDS: dict[int, tuple[str, str]] = {
    1: ("sounds/stereo_piano.wav", "Grand piano (45° right pan)"),
    2: ("sounds/stereo_synth.wav", "Synth (max. 64 left pan)"),
    3: ("sounds/stereo_synth_pan.wav", "Synth with changing pan from left to right"),
}


def choose_sound(choice: int) -> tuple[Path, str]:
    """Return the absolute file path and display title for the given choice.

    Args:
        choice: Integer key that must exist in :data:`SOUNDS`.

    Returns:
        A ``(file_path, title)`` tuple.

    Raises:
        KeyError: If *choice* is not a valid key in :data:`SOUNDS`.
    """
    relative_path, title = SOUNDS[choice]
    return SCRIPT_DIR / relative_path, title


def build_stereo_spectrogram(file_path: Path, scale: str, title: str) -> None:
    """Compute STFT for both stereo channels and render stacked spectrograms.

    Args:
        file_path: Path to the stereo WAV file.
        scale: Frequency-axis scale – ``"log"`` or ``"linear"``.
        title: Base plot title; the channel label is prepended automatically.
    """
    audio, sample_rate = librosa.load(file_path, mono=False)
    left = librosa.amplitude_to_db(np.abs(librosa.stft(audio[0])), ref=np.max)
    right = librosa.amplitude_to_db(np.abs(librosa.stft(audio[1])), ref=np.max)

    fig, axes = plt.subplots(nrows=2, ncols=1, sharex=True)

    img = librosa.display.specshow(
        left, y_axis=scale, x_axis="time", sr=sample_rate, ax=axes[0]
    )
    axes[0].set_title(f"Left Channel | {title}")
    axes[0].label_outer()

    librosa.display.specshow(right, y_axis=scale, x_axis="time", sr=sample_rate, ax=axes[1])
    axes[1].set_title(f"Right Channel | {title}")
    axes[1].label_outer()

    fig.colorbar(img, ax=axes, format="%+2.f dB")
    plt.show()


def main() -> None:
    """Prompt the user, optionally play the audio, and display the stereo spectrogram."""
    print("\n     WELCOME TO STEREO CHANNEL SOUND VISUALIZER\n")

    sound_choice = get_menu_choice(
        "Choose sound to visualize:",
        {key: title for key, (_, title) in SOUNDS.items()},
    )
    scale_choice = get_menu_choice(
        "Choose frequency scale:",
        {1: "Logarithmic", 2: "Linear"},
    )
    scale = "log" if scale_choice == 1 else "linear"

    play = input("     Play the sound sample before visualizing? (y/n) ").strip().lower()

    file_path, title = choose_sound(sound_choice)

    if play == "y":
        playsound(str(file_path))

    build_stereo_spectrogram(file_path, scale, title)


if __name__ == "__main__":
    main()
