# Copilot Instructions

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

**Python 3.10+ is required** — the codebase uses built-in generic type hints (`dict[int, str]`, `tuple[str, str]`) without `from __future__ import annotations`.

Linux-only system dependencies:
- Audio preview: `sudo apt install python3-gst-1.0 gstreamer1.0-plugins-good`
- Real-time visualizer: `sudo apt install libportaudio2`

There are no automated tests or linters configured.

## Architecture

Each script is a standalone visualizer that runs from the repository root. `utils.py` is the only shared module.

```
utils.py                    # Shared: choose_sound(), get_menu_choice()
mono_channel_visualizer.py  # STFT spectrogram — mono files
stereo_channel_visualizer.py# Stacked L/R spectrograms — stereo files
stereo_image_analyzer.py    # ICLD panning angle scatter plot — hardcoded to stereo_piano.wav
animation_sine_wave.py      # Standalone Matplotlib animation, no audio
realtime_3d_visualizer.py   # Threaded: sounddevice audio → queue → vispy 3D surface
sounds/                     # WAV sample files
```

### `realtime_3d_visualizer.py` threading model

Two classes cooperate across threads:

- **`AudioStreamer`** — `sounddevice` OutputStream callback runs on the audio thread. It fills the sound-card buffer and simultaneously pushes mono PCM chunks to a `queue.Queue`. The callback must never block; frames are silently dropped (`put_nowait`) if the queue is full.
- **`WaterfallVisualizer`** — a vispy `Timer` fires on the main/UI thread every 30 ms. It drains the queue, runs FFT → log-spaced display bins → dB normalisation, rolls the 2D grid, and calls `SurfacePlot.set_data` to push Z-values and RGBA colours to the GPU.

## Key Conventions

### SOUNDS catalogue pattern
Every interactive script defines a module-level `SOUNDS` dict:
```python
SOUNDS: dict[int, tuple[str, str]] = {
    1: ("sounds/filename.wav", "Human-readable title"),
}
```
`utils.choose_sound(choice, SOUNDS, SCRIPT_DIR)` resolves the relative path against `Path(__file__).parent`.

### Script structure
All scripts follow the same layout:
1. Module docstring with one-line summary, longer description, and `Usage::` block
2. Module-level constants in `UPPER_SNAKE_CASE`
3. Pure functions with Google-style docstrings (Args / Returns / Raises)
4. A `main()` function handling user prompts and orchestration
5. `if __name__ == "__main__": main()` guard

### Type annotations
- Use `npt.NDArray[np.float32]` / `npt.NDArray[np.float64]` for NumPy arrays (imported as `import numpy.typing as npt`)
- Prefer `tuple[A, B]` and `dict[K, V]` (Python 3.10 built-in generics, not `typing.Tuple`/`typing.Dict`)
- `threading.Event | None` union syntax (not `Optional`)

### Audio pipeline (non-realtime scripts)
```python
audio, sample_rate = librosa.load(file_path, mono=True/False)
spectrogram = librosa.amplitude_to_db(np.abs(librosa.stft(audio)), ref=np.max)
librosa.display.specshow(spectrogram, y_axis="log"/"linear", x_axis="time", sr=sample_rate, ax=ax)
```
Stereo files: `audio[0]` = left channel, `audio[1]` = right channel.
