# sound-visualizer-prototype

A collection of Python scripts for visualizing digitized audio — exploring
what a piece of sound becomes when it is represented as numbers.

Originally created during a research project at ITU in the fall of 2021,
and subsequently modernized to follow current Python standards (PEP 8,
type hints, docstrings, proper entry-point guards).

---

## Scripts

| Script | Description |
|---|---|
| `mono_channel_visualizer.py` | Displays a dB-scaled spectrogram for a mono audio file. |
| `stereo_channel_visualizer.py` | Displays stacked left/right spectrograms for a stereo audio file. |
| `animation_sine_wave.py` | Animated travelling sine wave — conceptual illustration of a periodic waveform. |
| `stereo_image_analyzer.py` | Estimates the panning angle per frequency bin and plots the stereo image. |

## Setup

```bash
pip install -r requirements.txt
```

## Usage

Each script is self-contained and runs interactively from the command line:

```bash
python mono_channel_visualizer.py
python stereo_channel_visualizer.py
python animation_sine_wave.py
python stereo_image_analyzer.py
```

Audio samples are located in the `sounds/` directory.
