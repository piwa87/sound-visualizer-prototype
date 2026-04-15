"""Mono channel sound visualizer.

Loads a mono audio file, computes its short-time Fourier transform (STFT),
and displays a dB-scaled spectrogram.

Usage::

    python mono_channel_visualizer.py
"""

from pathlib import Path

import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import sounddevice as sd
import soundfile as sf

from utils import choose_sound, get_menu_choice

SCRIPT_DIR = Path(__file__).parent

SOUNDS: dict[int, tuple[str, str]] = {
    1: ("sounds/01_kick_drum.wav", "Kick drum (2 last hits with reverb)"),
    2: ("sounds/02_synth_eq.wav", "Lead synthesizer with EQ"),
    3: ("sounds/03_horns.wav", "Groovy band with horns"),
    4: ("sounds/04_explosion.wav", "Explosion"),
    5: ("sounds/05_synth_pad.wav", "Rhythmic synth pad with a filter"),
}


def build_spectrogram(file_path: Path, scale: str, title: str) -> None:
    """Compute the STFT and render a dB-scaled spectrogram.

    Args:
        file_path: Path to the mono WAV file.
        scale: Frequency-axis scale – ``"log"`` or ``"linear"``.
        title: Plot title shown above the spectrogram.
    """
    audio, sample_rate = librosa.load(file_path, mono=True)
    spectrogram = librosa.amplitude_to_db(np.abs(librosa.stft(audio)), ref=np.max)

    fig, ax = plt.subplots()
    img = librosa.display.specshow(
        spectrogram, y_axis=scale, x_axis="time", sr=sample_rate, ax=ax
    )
    ax.set_title(title)
    ax.set_xlabel("Time in seconds")
    ax.label_outer()
    fig.colorbar(img, ax=ax, format="%+2.f dB")
    plt.show()


def main() -> None:
    """Prompt the user, optionally play the audio, and display the spectrogram."""
    print("\n     WELCOME TO SINGLE CHANNEL SOUND VISUALIZER\n")

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

    file_path, title = choose_sound(sound_choice, SOUNDS, SCRIPT_DIR)

    if play == "y":
        data, samplerate = sf.read(str(file_path))
        sd.play(data, samplerate)
        sd.wait()

    build_spectrogram(file_path, scale, title)


if __name__ == "__main__":
    main()
