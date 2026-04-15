"""Stereo image analyzer.

Estimates the perceived panning angle for every time-frequency bin of a
stereo audio file using the inter-channel level difference (ICLD) and
renders the result as a scatter plot of angle vs. frequency — the classic
"stereo image" view.

The angle formula used is::

    angle ≈ arcsin( (L_dB − R_dB) / ((L_dB + R_dB) · sin(ref_angle)) )

A positive angle means the sound is panned to the right; negative means
panned to the left.

Usage::

    python stereo_image_analyzer.py
"""

from pathlib import Path

import librosa
import numpy as np
import numpy.typing as npt
import matplotlib.pyplot as plt

FILENAME: Path = Path(__file__).parent / "sounds/stereo_piano.wav"

HOP_LENGTH: int = 512
REFERENCE_ANGLE_DEG: float = 30.0
ANGLE_LIMIT_DEG: float = 90.0
MAX_FREQUENCY_HZ: float = 20_000.0


def compute_stereo_angles(
    left_db: npt.NDArray[np.float64],
    right_db: npt.NDArray[np.float64],
    reference_angle_deg: float = REFERENCE_ANGLE_DEG,
) -> npt.NDArray[np.float64]:
    """Estimate the panning angle (degrees) for each time-frequency bin.

    Uses the inter-channel level difference (ICLD):

        angle ≈ arcsin( (L − R) / ((L + R) · sin(ref)) )

    Bins where both channels are silent (denominator == 0) are assigned
    an angle of 0° (centre).  The ratio is clamped to ``[−1, 1]`` before
    the arcsin to handle numerical noise.

    Args:
        left_db: dB-scaled STFT magnitude for the left channel,
            shape ``(n_freq_bins, n_frames)``.
        right_db: dB-scaled STFT magnitude for the right channel,
            same shape as *left_db*.
        reference_angle_deg: Reference pan angle used for normalisation
            (default 30°).

    Returns:
        Array of panning angles in degrees with the same shape as the inputs.
    """
    if reference_angle_deg == 0.0:
        raise ValueError("reference_angle_deg must be non-zero to avoid division by zero.")
    ref_sin = np.sin(np.deg2rad(reference_angle_deg))
    denominator = left_db + right_db
    with np.errstate(invalid="ignore", divide="ignore"):
        ratio = np.where(denominator != 0.0, (left_db - right_db) / denominator, 0.0)
    angles: npt.NDArray[np.float64] = np.rad2deg(
        np.arcsin(np.clip(ratio / ref_sin, -1.0, 1.0))
    )
    return angles


def plot_stereo_image(
    angles: npt.NDArray[np.float64],
    sample_rate: int,
    hop_length: int = HOP_LENGTH,
) -> None:
    """Render a scatter plot of panning angle vs. frequency.

    Each point represents one time-frequency observation.  Points near
    the centre line (0°) indicate mono-compatible content; points further
    out indicate hard panning.

    Args:
        angles: Panning-angle array produced by :func:`compute_stereo_angles`,
            shape ``(n_freq_bins, n_frames)``.
        sample_rate: Audio sample rate in Hz, used to convert bin indices to
            frequencies.
        hop_length: STFT hop length that was used when computing the STFT.
    """
    n_fft = (angles.shape[0] - 1) * 2
    freqs = librosa.fft_frequencies(sr=sample_rate, n_fft=n_fft)

    # Flatten: one observation per (frequency-bin, time-frame) pair
    angle_flat = angles.ravel()
    freq_flat = np.tile(freqs, angles.shape[1])

    fig, ax = plt.subplots()
    ax.set_xlim(-ANGLE_LIMIT_DEG, ANGLE_LIMIT_DEG)
    ax.set_ylim(0, MAX_FREQUENCY_HZ)
    ax.set_title("Stereo Image")
    ax.set_xlabel("Angle of stereo image (degrees)")
    ax.set_ylabel("Frequency (Hz)")
    ax.axvline(x=0, color="b", linestyle="-", linewidth=0.8, label="Centre")
    ax.label_outer()
    ax.scatter(angle_flat, freq_flat, s=0.5, alpha=0.3, color="steelblue")
    ax.legend()
    plt.show()


def main() -> None:
    """Load the stereo piano sample and display its stereo image."""
    audio, sample_rate = librosa.load(FILENAME, mono=False)

    left_magnitude = np.abs(librosa.stft(audio[0], hop_length=HOP_LENGTH))
    right_magnitude = np.abs(librosa.stft(audio[1], hop_length=HOP_LENGTH))

    left_db = librosa.amplitude_to_db(left_magnitude, ref=np.max)
    right_db = librosa.amplitude_to_db(right_magnitude, ref=np.max)

    angles = compute_stereo_angles(left_db, right_db)

    plot_stereo_image(angles, sample_rate)


if __name__ == "__main__":
    main()
