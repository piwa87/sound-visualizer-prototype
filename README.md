# sound-visualizer-prototype

A collection of Python scripts for visualizing digitized audio — exploring
what a piece of sound becomes when it is represented as numbers.

Originally created during a research project at ITU in the fall of 2021,
and subsequently modernized to follow current Python standards (PEP 8,
type hints, docstrings, proper entry-point guards).

---

## Prerequisites

- **Python 3.10 or later** (type hints such as `dict[int, str]` require 3.10+)
- **pip** (bundled with all modern Python installations)

> **Linux users:** `playsound` relies on GStreamer for WAV playback. Install the
> required libraries before running any script that offers audio preview:
> ```bash
> sudo apt install python3-gst-1.0 gstreamer1.0-plugins-good
> ```

> **Linux users (real-time visualizer):** `sounddevice` requires PortAudio. Install it before running `realtime_3d_visualizer.py`:
> ```bash
> sudo apt install libportaudio2
> ```

---

## Setup

Clone the repository (if you haven't already) and install the Python
dependencies into a virtual environment:

```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
.venv\Scripts\activate         # Windows

# 2. Install dependencies
pip install -r requirements.txt
```

The `requirements.txt` installs:

| Package | Purpose |
|---|---|
| `librosa` | Audio loading, STFT computation, spectrogram display |
| `matplotlib` | Plotting and animations |
| `numpy` | Numerical array operations |
| `playsound` | Optional audio preview before visualizing |
| `sounddevice` | Real-time audio streaming (chunk-by-chunk playback) |
| `soundfile` | WAV/FLAC file reading for the real-time visualizer |
| `vispy` | OpenGL-accelerated 3D surface rendering |
| `PyOpenGL` | OpenGL backend required by vispy |

---

## Scripts

| Script | Description |
|---|---|
| `mono_channel_visualizer.py` | Displays a dB-scaled spectrogram for a mono audio file. |
| `stereo_channel_visualizer.py` | Displays stacked left/right spectrograms for a stereo audio file. |
| `stereo_image_analyzer.py` | Estimates the panning angle per frequency bin and plots the stereo image. |
| `animation_sine_wave.py` | Animated travelling sine wave — conceptual illustration of a periodic waveform. |
| `realtime_3d_visualizer.py` | **Real-time** 3D waterfall: plays audio while rendering a live OpenGL spectrogram surface. |

---

## Running the scripts

All scripts are self-contained and run from the repository root. Make sure the
virtual environment is active before running them.

### Mono channel visualizer

```bash
python mono_channel_visualizer.py
```

Prompts you to:
1. Pick one of five mono audio samples (kick drum, synth, horns, explosion, synth pad).
2. Choose a frequency scale — **logarithmic** (more perceptually natural) or **linear**.
3. Optionally play the audio sample before the spectrogram is displayed.

### Stereo channel visualizer

```bash
python stereo_channel_visualizer.py
```

Prompts you to:
1. Pick one of three stereo samples (grand piano, synth left-panned, synth with moving pan).
2. Choose a frequency scale — **logarithmic** or **linear**.
3. Optionally play the audio sample before the spectrograms are displayed.

Renders two vertically stacked spectrograms: one for the left channel and one
for the right channel.

### Stereo image analyzer

```bash
python stereo_image_analyzer.py
```

No prompts — loads `sounds/stereo_piano.wav` automatically and opens a scatter
plot showing the estimated panning angle (degrees) versus frequency (Hz) for
every time-frequency bin. Points near 0° are centred; positive values are
panned right, negative values are panned left.

### Animated sine wave

```bash
python animation_sine_wave.py
```

No prompts — opens a looping Matplotlib animation of a travelling sine wave.
Useful as a conceptual illustration of a periodic waveform before digitisation.
Close the window to exit.

### Real-time 3D audio waterfall *(new)*

```bash
python realtime_3d_visualizer.py
```

Prompts you to pick one of eight audio samples (all five mono samples plus the
three stereo samples).  Once selected, the script:

1. Opens an OpenGL window showing a 3D spectrogram surface — frequency on the
   X axis, time history on the Y axis, and amplitude (dB) on the Z axis,
   colour-mapped from dark (quiet) to bright yellow/white (loud).
2. Starts playing the chosen audio file through your default output device.
3. Updates the 3D surface in real time (~33 FPS) as each audio chunk plays,
   so the visualization is in sync with what you hear.

**Controls while the window is open:**

| Action | Effect |
|---|---|
| Left-drag | Rotate the 3D surface |
| Scroll wheel | Zoom in / out |
| Right-drag | Pan |

The window closes automatically when playback ends.

**How it works:**

Audio is read in 2048-sample chunks (~46 ms at 44.1 kHz) via a
`sounddevice` OutputStream callback.  Each callback fills the sound-card
buffer and simultaneously pushes a mono mix of the chunk to a thread-safe
queue.  A vispy `Timer` fires on the main thread every 30 ms, drains the
queue, computes a 4 096-point FFT, maps the result to 256 log-spaced
frequency display bins, converts to dB, and feeds the normalised values to a
vispy `SurfacePlot` for GPU rendering.

---

## Audio samples

All sample files are in the `sounds/` directory:

| File | Used by |
|---|---|
| `01_kick_drum.wav` | Mono visualizer |
| `02_synth_eq.wav` | Mono visualizer |
| `03_horns.wav` | Mono visualizer |
| `04_explosion.wav` | Mono visualizer |
| `05_synth_pad.wav` | Mono visualizer |
| `stereo_piano.wav` | Stereo visualizer, Stereo image analyzer, Real-time 3D visualizer |
| `stereo_synth.wav` | Stereo visualizer, Real-time 3D visualizer |
| `stereo_synth_pan.wav` | Stereo visualizer, Real-time 3D visualizer |
