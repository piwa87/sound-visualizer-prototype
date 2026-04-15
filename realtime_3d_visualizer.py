"""Real-time 3D audio waterfall visualizer.

Plays an audio file while simultaneously rendering a live 3D spectrogram
waterfall.  Audio is streamed chunk-by-chunk via ``sounddevice``; each
chunk is transformed to the frequency domain with a short FFT and appended
as a new row to a rolling magnitude grid that drives a vispy
``SurfacePlot``.

Architecture
------------
``sounddevice`` OutputStream callback  (audio thread)
    → pushes raw mono PCM chunk to ``queue.Queue``

vispy ``Timer`` callback  (main / UI thread)
    → drains queue
    → FFT magnitude → amplitude in dB
    → rolls the 2D grid and updates the surface-plot Z-data

Axes
----
* X — frequency (Hz, log-spaced display bins)
* Y — time (most recent frame at Y = 0, oldest at Y = 1)
* Z — amplitude (dB above noise floor, normalised to [0, 1])

Controls
--------
* Left-drag  — rotate the 3D surface
* Scroll     — zoom in / out
* Right-drag — pan

Usage::

    python realtime_3d_visualizer.py
"""

import queue
import threading
from pathlib import Path

import numpy as np
import numpy.typing as npt
import sounddevice as sd
import soundfile as sf
import vispy.app
import vispy.scene
from vispy.color import get_colormap

from utils import choose_sound, get_menu_choice

SCRIPT_DIR = Path(__file__).parent

# ── Sound catalogue (mono + stereo) ──────────────────────────────────────────
SOUNDS: dict[int, tuple[str, str]] = {
    1: ("sounds/01_kick_drum.wav", "Kick drum"),
    2: ("sounds/02_synth_eq.wav", "Lead synthesizer with EQ"),
    3: ("sounds/03_horns.wav", "Groovy band with horns"),
    4: ("sounds/04_explosion.wav", "Explosion"),
    5: ("sounds/05_synth_pad.wav", "Rhythmic synth pad"),
    6: ("sounds/stereo_piano.wav", "Grand piano"),
    7: ("sounds/stereo_synth.wav", "Synth (left-panned)"),
    8: ("sounds/stereo_synth_pan.wav", "Synth (panning left → right)"),
}

# ── DSP parameters ────────────────────────────────────────────────────────────
CHUNK_SIZE: int = 2048      # Frames per audio callback (~46 ms at 44.1 kHz)
N_FFT: int = 4096           # FFT size → controls frequency resolution
N_TIME_FRAMES: int = 120    # Rolling history depth (Y axis length)
N_FREQ_DISPLAY: int = 256   # Number of display frequency bins (X axis length)
DB_FLOOR: float = -80.0     # Noise floor in dB; amplitudes below are clipped

# ── Visualizer parameters ─────────────────────────────────────────────────────
CANVAS_SIZE: tuple[int, int] = (1024, 700)
UPDATE_INTERVAL_S: float = 0.030   # ~33 FPS timer tick


# ─────────────────────────────────────────────────────────────────────────────
# Audio streaming
# ─────────────────────────────────────────────────────────────────────────────

class AudioStreamer:
    """Streams a WAV file via ``sounddevice`` while feeding PCM chunks to a queue.

    The ``sounddevice`` OutputStream callback runs on a dedicated audio thread.
    It fills the sound-card output buffer with the next ``chunk_size`` frames
    from the pre-loaded file and simultaneously pushes the same PCM data
    (mixed down to mono) to *audio_queue* for processing by the visualizer.

    Args:
        file_path: Path to the audio file (WAV, FLAC, etc.).
        chunk_size: Number of audio frames per callback block.
        audio_queue: Thread-safe queue that receives mono PCM chunks
            (``numpy.ndarray`` of ``float32``) for the visualization thread.
    """

    def __init__(
        self,
        file_path: Path,
        chunk_size: int,
        audio_queue: "queue.Queue[npt.NDArray[np.float32] | None]",
    ) -> None:
        self._data, self._sample_rate = sf.read(
            file_path, dtype="float32", always_2d=True
        )
        # Mono mix used for the FFT; full multi-channel data for playback
        self._mono: npt.NDArray[np.float32] = self._data.mean(axis=1)
        self._chunk_size = chunk_size
        self._queue = audio_queue
        self._pos: int = 0
        self.finished = threading.Event()

    @property
    def sample_rate(self) -> int:
        """Sample rate of the loaded audio file in Hz."""
        return self._sample_rate

    def _callback(
        self,
        outdata: npt.NDArray[np.float32],
        frames: int,
        time_info: object,
        status: sd.CallbackFlags,
    ) -> None:
        """sounddevice OutputStream callback — runs on the audio thread.

        Fills *outdata* with the next block of PCM frames and pushes the
        corresponding mono slice to the visualization queue.  The last block
        is zero-padded to *frames* length and triggers the ``finished`` event.
        """
        end = self._pos + frames
        chunk = self._data[self._pos:end]

        if len(chunk) < frames:
            # Pad the final (short) block with silence
            pad = np.zeros(
                (frames - len(chunk), self._data.shape[1]), dtype=np.float32
            )
            chunk = np.vstack([chunk, pad])
            self.finished.set()

        outdata[:] = chunk

        # Push mono slice to the visualization queue (non-blocking)
        mono_end = min(end, len(self._mono))
        mono_chunk = self._mono[self._pos:mono_end].copy()
        try:
            self._queue.put_nowait(mono_chunk)
        except queue.Full:
            pass  # Drop the frame rather than block the audio thread

        self._pos = min(end, len(self._data))

    def start(self) -> sd.OutputStream:
        """Open and start the ``sounddevice`` OutputStream.

        Returns:
            The active :class:`sounddevice.OutputStream`.  The caller must
            keep this reference alive for the duration of playback.
        """
        stream = sd.OutputStream(
            samplerate=self._sample_rate,
            channels=self._data.shape[1],
            dtype="float32",
            blocksize=self._chunk_size,
            callback=self._callback,
        )
        stream.start()
        return stream


# ─────────────────────────────────────────────────────────────────────────────
# 3-D visualizer
# ─────────────────────────────────────────────────────────────────────────────

class WaterfallVisualizer:
    """Real-time 3D spectrogram waterfall renderer powered by vispy.

    Maintains a rolling 2D dB-magnitude grid (shape ``[N_TIME_FRAMES,
    N_FREQ_DISPLAY]``) and updates a vispy ``SurfacePlot`` on every timer tick.
    Each new audio chunk is projected onto log-spaced frequency display bins,
    converted to dB, normalised to ``[0, 1]``, and colour-mapped via the
    *fire* colormap before being sent to the GPU.

    Args:
        audio_queue: Queue producing mono PCM chunks from :class:`AudioStreamer`.
        sample_rate: Audio sample rate in Hz.
        n_fft: FFT size (higher → finer frequency resolution).
        n_time_frames: Number of historical frames to display (Y axis depth).
        n_freq_display: Number of log-spaced frequency display bins (X axis).
        db_floor: Noise floor in dB; amplitudes below this are clipped to zero.
        finished_event: When set and the queue is empty, the visualizer exits.
        title: Window title string.
    """

    def __init__(
        self,
        audio_queue: "queue.Queue[npt.NDArray[np.float32] | None]",
        sample_rate: int,
        n_fft: int = N_FFT,
        n_time_frames: int = N_TIME_FRAMES,
        n_freq_display: int = N_FREQ_DISPLAY,
        db_floor: float = DB_FLOOR,
        finished_event: threading.Event | None = None,
        title: str = "Real-time 3D Audio Waterfall",
    ) -> None:
        self._queue = audio_queue
        self._n_fft = n_fft
        self._n_time_frames = n_time_frames
        self._db_floor = db_floor
        self._finished_event = finished_event
        self._cmap = get_colormap("fire")

        # Build log-spaced display bin index mapping ──────────────────────────
        fft_freqs = np.fft.rfftfreq(n_fft, d=1.0 / sample_rate)
        n_bins = len(fft_freqs)
        log_indices = np.unique(
            np.round(
                np.logspace(0, np.log10(n_bins - 1), n_freq_display)
            ).astype(int)
        )
        self._display_indices: npt.NDArray[np.intp] = log_indices
        # Actual display count may differ slightly after deduplication
        self._n_freq: int = len(log_indices)

        # Rolling dB grid — shape (n_time_frames, n_freq) ─────────────────────
        self._grid = np.full(
            (n_time_frames, self._n_freq), db_floor, dtype=np.float32
        )

        self._canvas, self._surface = self._build_scene(title)
        self._timer: vispy.app.Timer | None = None

    # ── Scene construction ────────────────────────────────────────────────────

    def _build_scene(
        self, title: str
    ) -> tuple[vispy.scene.SceneCanvas, vispy.scene.visuals.SurfacePlot]:
        """Create the vispy canvas, camera, and initial flat surface plot."""
        canvas = vispy.scene.SceneCanvas(
            title=title,
            size=CANVAS_SIZE,
            bgcolor="#0d0d1a",
            show=True,
        )
        view = canvas.central_widget.add_view()
        view.camera = vispy.scene.cameras.TurntableCamera(
            fov=40, distance=3.0, elevation=30, azimuth=-60
        )

        # Normalised coordinate axes: X ∈ [0,1] (freq), Y ∈ [0,1] (time)
        xs = np.linspace(0.0, 1.0, self._n_freq, dtype=np.float32)
        ys = np.linspace(0.0, 1.0, self._n_time_frames, dtype=np.float32)
        z0 = np.zeros((self._n_time_frames, self._n_freq), dtype=np.float32)

        # vispy expects z shape (len(x), len(y)) == (n_freq, n_time_frames),
        # so transpose the grid which is stored as (n_time_frames, n_freq).
        # Colors are not passed here to avoid a vispy bug where set_vertex_colors
        # is called before set_faces during construction; they are applied on the
        # first update() tick instead.
        surface = vispy.scene.visuals.SurfacePlot(
            x=xs,
            y=ys,
            z=z0.T,
            parent=view.scene,
        )
        return canvas, surface

    # ── Per-frame DSP ─────────────────────────────────────────────────────────

    def _z_to_colors(
        self, z_norm: npt.NDArray[np.float32]
    ) -> npt.NDArray[np.float32]:
        """Map a normalised Z grid to per-vertex RGBA via the fire colormap.

        Args:
            z_norm: 2D array of shape ``(n_time_frames, n_freq)`` with values
                in ``[0, 1]``.

        Returns:
            Float32 RGBA array of shape ``(n_time_frames * n_freq, 4)``.
        """
        return self._cmap[z_norm.ravel()].rgba.astype(np.float32)

    def _process_chunk(
        self, chunk: npt.NDArray[np.float32]
    ) -> npt.NDArray[np.float32]:
        """FFT → log-spaced display bins → dB normalisation → 1D row.

        A Hann window is applied before the FFT to suppress spectral leakage
        caused by discontinuities at block boundaries.

        Args:
            chunk: Mono PCM samples for one audio block.

        Returns:
            Float32 array of shape ``(n_freq,)`` with values in
            ``[db_floor, 0]``.
        """
        window = np.hanning(len(chunk)).astype(np.float32)
        spectrum = np.abs(np.fft.rfft(chunk * window, n=self._n_fft))
        display = spectrum[self._display_indices]
        ref = float(display.max()) if display.max() > 0.0 else 1.0
        db = 20.0 * np.log10(np.maximum(display / ref, 1e-10))
        return np.maximum(db, self._db_floor).astype(np.float32)

    # ── Timer callback ────────────────────────────────────────────────────────

    def update(self, event: object) -> None:
        """vispy ``Timer`` callback — drain the queue, scroll, and redraw.

        Drains all available chunks from the queue (keeping only the latest
        computed row to avoid visual lag), rolls the grid by one step, and
        calls ``SurfacePlot.set_data`` to push the new Z-values and colours
        to the GPU.

        When ``finished_event`` is set *and* the queue is empty, the vispy
        event loop is stopped automatically.
        """
        # Auto-close when playback has finished and the queue is fully drained
        if (
            self._finished_event is not None
            and self._finished_event.is_set()
            and self._queue.empty()
        ):
            vispy.app.quit()
            return

        new_row: npt.NDArray[np.float32] | None = None
        while True:
            try:
                chunk = self._queue.get_nowait()
                new_row = self._process_chunk(chunk)
            except queue.Empty:
                break

        if new_row is None:
            return

        # Scroll: push all existing rows back by one; newest row goes to index 0
        self._grid = np.roll(self._grid, 1, axis=0)
        self._grid[0] = new_row

        # Normalise dB grid to [0, 1] for the Z axis
        z_norm = (
            (self._grid - self._db_floor) / (-self._db_floor)
        ).astype(np.float32)

        self._surface.set_data(z=z_norm.T, colors=self._z_to_colors(z_norm.T))

    # ── Entry point ───────────────────────────────────────────────────────────

    def run(self) -> None:
        """Start the update timer and enter the vispy event loop.

        Blocks until the window is closed or playback finishes.
        """
        self._timer = vispy.app.Timer(
            interval=UPDATE_INTERVAL_S,
            connect=self.update,
            start=True,
        )
        vispy.app.run()
        self._timer.stop()


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """Prompt for a sound, stream it, and launch the real-time 3D waterfall."""
    print("\n     WELCOME TO THE REAL-TIME 3D AUDIO WATERFALL VISUALIZER\n")
    print("     Controls: left-drag to rotate · scroll to zoom · right-drag to pan\n")

    sound_choice = get_menu_choice(
        "Choose sound to visualize:",
        {key: title for key, (_, title) in SOUNDS.items()},
    )
    file_path, title = choose_sound(sound_choice, SOUNDS, SCRIPT_DIR)

    audio_queue: queue.Queue[npt.NDArray[np.float32] | None] = queue.Queue(
        maxsize=64
    )
    streamer = AudioStreamer(file_path, CHUNK_SIZE, audio_queue)
    visualizer = WaterfallVisualizer(
        audio_queue=audio_queue,
        sample_rate=streamer.sample_rate,
        n_fft=N_FFT,
        n_time_frames=N_TIME_FRAMES,
        n_freq_display=N_FREQ_DISPLAY,
        db_floor=DB_FLOOR,
        finished_event=streamer.finished,
        title=f"3D Waterfall — {title}",
    )

    stream = streamer.start()
    try:
        visualizer.run()
    finally:
        stream.stop()
        stream.close()


if __name__ == "__main__":
    main()
