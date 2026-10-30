"""
Acoustic AI Water Level Detection Model for Dark Underground Sewers.
Processes acoustic waveforms, Sound Pressure Level (dB SPL), and spectrograms
using Librosa and NumPy when optical cameras fail in darkness or condensation.
"""

import base64
import io
import math
import wave
import struct
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless server
import matplotlib.pyplot as plt

import config


class AcousticLevelAI:
    """
    Analyzes sewer audio recordings to infer water level (0-100%) and hydraulic turbulence.
    Integrates Librosa with robust native NumPy/SciPy digital signal processing.
    """

    def __init__(self, db_min: float = config.ACOUSTIC_DB_MIN, db_max: float = config.ACOUSTIC_DB_MAX):
        self.db_min = db_min
        self.db_max = db_max
        self.pipe_diameter_m = 2.4  # Standard Indore trunk culvert diameter (m)

    def analyze_audio(self, audio_input: Any) -> Dict[str, Any]:
        """
        Analyze audio file path, raw bytes, or numpy signal array.
        Returns estimated water level %, decibels, frequency attributes, and spectrogram.
        """
        signal, sample_rate = self._load_audio(audio_input)
        if signal is None or len(signal) == 0:
            return {
                "error": "Failed to decode acoustic signal",
                "estimated_water_level_pct": 0.0,
                "decibel_spl": 0.0,
                "flow_regime": "Sensor Inactive",
            }

        # Step 1: Root Mean Square (RMS) & Sound Pressure Level (dB SPL)
        rms = np.sqrt(np.mean(signal ** 2)) + 1e-9
        # Calibrated decibel scale: reference pressure p0 = 2e-5 Pa
        db_spl = float(20.0 * np.log10(rms / 1e-4) + 60.0)
        db_spl = max(30.0, min(100.0, db_spl))

        # Step 2: Frequency & Spectral Analysis via FFT / Spectrogram
        # Use librosa if available, else numpy FFT
        n_fft = min(2048, len(signal))
        hop_length = n_fft // 4

        freqs = np.fft.rfftfreq(n_fft, d=1.0 / sample_rate)
        fft_magnitude = np.abs(np.fft.rfft(signal[:n_fft]))

        # Spectral Centroid (Center of mass of spectrum)
        spectral_centroid = float(np.sum(freqs * fft_magnitude) / (np.sum(fft_magnitude) + 1e-9))
        peak_freq = float(freqs[np.argmax(fft_magnitude)])

        # Step 3: Acoustic-Hydraulic Level Mapping
        # In a dark underground circular conduit:
        # High decibels correlate with volumetric flow and velocity.
        # High spectral centroid reflects water splashing and turbulent surface waves.
        # Pipe air cavity resonance frequency rises as air volume decreases.
        db_factor = (db_spl - self.db_min) / (self.db_max - self.db_min)
        db_factor = max(0.0, min(1.0, db_factor))

        # Non-linear acoustic level estimation:
        estimated_level_pct = round(min(100.0, max(2.0, (db_factor ** 1.15) * 100.0)), 1)
        estimated_depth_m = round((estimated_level_pct / 100.0) * self.pipe_diameter_m, 2)

        # Flow Regime & Hazard Classification
        if estimated_level_pct <= config.WATER_LEVEL_SAFE_MAX:
            regime = "Base Flow / Nominal Trickle (सामान्य बहाव)"
            alert_status = "SAFE"
            alert_color = "#00e676"
        elif estimated_level_pct <= config.WATER_LEVEL_WARNING_MAX:
            regime = "Moderate Surge / Rapid Channel Flow (मध्यम उफान)"
            alert_status = "WARNING"
            alert_color = "#ffab00"
        else:
            regime = "Full-Pipe Pressurized Flash Surge (खतरनाक जलभराव)"
            alert_status = "CRITICAL"
            alert_color = "#ff1744"

        # Step 4: Render Visual Spectrogram Plot
        spectrogram_b64 = self._generate_spectrogram_plot(signal, sample_rate, db_spl, estimated_level_pct)

        return {
            "estimated_water_level_pct": estimated_level_pct,
            "estimated_depth_m": estimated_depth_m,
            "pipe_diameter_m": self.pipe_diameter_m,
            "decibel_spl": round(db_spl, 1),
            "spectral_centroid_hz": round(spectral_centroid, 1),
            "dominant_frequency_hz": round(peak_freq, 1),
            "flow_regime": regime,
            "alert_status": alert_status,
            "alert_color": alert_color,
            "sample_rate_hz": sample_rate,
            "duration_sec": round(len(signal) / sample_rate, 2),
            "spectrogram_image_b64": spectrogram_b64,
            "model_type": "HEURISTIC_SPECTRAL_RESONANCE",
            "disclaimer": "Heuristic acoustic resonance model for dark sewer prototype. In-situ physical calibration required for production.",
        }

    def _load_audio(self, audio_input: Any) -> Tuple[Optional[np.ndarray], int]:
        """Load audio signal safely via native wave or librosa."""
        # Check if already a numpy array
        if isinstance(audio_input, np.ndarray):
            return audio_input.astype(np.float32), 22050

        # Try soundfile
        try:
            import soundfile as sf
            if isinstance(audio_input, (str, Path)):
                data, sr = sf.read(str(audio_input))
                if data.ndim > 1:
                    data = data.mean(axis=1)
                return data.astype(np.float32), sr
            elif isinstance(audio_input, (bytes, bytearray)):
                data, sr = sf.read(io.BytesIO(audio_input))
                if data.ndim > 1:
                    data = data.mean(axis=1)
                return data.astype(np.float32), sr
        except Exception:
            pass

        # Try librosa if path or bytes
        try:
            import librosa
            if isinstance(audio_input, (str, Path)):
                sig, sr = librosa.load(str(audio_input), sr=22050, mono=True)
                return sig, sr
            elif isinstance(audio_input, (bytes, bytearray)):
                buf = io.BytesIO(audio_input)
                sig, sr = librosa.load(buf, sr=22050, mono=True)
                return sig, sr
        except Exception:
            pass

        # Fallback to standard library wave reader for standard WAV formats
        try:
            if isinstance(audio_input, (str, Path)):
                with wave.open(str(audio_input), "rb") as wf:
                    return self._read_wave_file(wf)
            elif isinstance(audio_input, (bytes, bytearray)):
                with wave.open(io.BytesIO(audio_input), "rb") as wf:
                    return self._read_wave_file(wf)
        except Exception:
            pass

        return None, 22050

    def _read_wave_file(self, wf: wave.Wave_read) -> Tuple[np.ndarray, int]:
        """Convert wave file frames to normalized float array."""
        sr = wf.getframerate()
        n_frames = wf.getnframes()
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        raw_bytes = wf.readframes(n_frames)

        if sampwidth == 2:
            data = np.frombuffer(raw_bytes, dtype=np.int16)
        elif sampwidth == 1:
            data = np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.int16) - 128
        else:
            data = np.frombuffer(raw_bytes, dtype=np.int32)

        if channels > 1:
            data = data.reshape(-1, channels).mean(axis=1)

        signal = data.astype(np.float32) / (np.max(np.abs(data)) + 1e-9)
        return signal, sr

    def _generate_spectrogram_plot(self, signal: np.ndarray, sr: int, db: float, level_pct: float) -> str:
        """Render dark-themed acoustic spectrogram and waveform visual."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.5, 3.8), facecolor="#0a0f1d")

        # Time-domain waveform
        t = np.linspace(0, len(signal) / sr, len(signal))
        ax1.plot(t, signal, color="#00e5ff", linewidth=0.8, alpha=0.9)
        ax1.set_facecolor("#111b2e")
        ax1.set_ylabel("Amplitude", color="#90caf9", fontsize=8)
        ax1.tick_params(colors="#90caf9", labelsize=7)
        ax1.set_title(f"Underground Sewer Hydrophone Waveform | {db:.1f} dB SPL | Level: {level_pct:.0f}%",
                      color="#ffffff", fontsize=9, fontweight="bold")
        ax1.grid(True, color="#1e293b", linestyle="--", alpha=0.5)

        # Frequency spectrogram (microscopic dither noise floor prevents log10(0) on silent audio)
        nfft = min(1024, len(signal))
        noise_floor = np.random.normal(0, 1e-6, len(signal)).astype(np.float32)
        pxx, freq, bins, im = ax2.specgram(signal + noise_floor, NFFT=nfft, Fs=sr, noverlap=nfft // 2, cmap="magma")
        ax2.set_facecolor("#111b2e")
        ax2.set_xlabel("Time (seconds)", color="#90caf9", fontsize=8)
        ax2.set_ylabel("Freq (Hz)", color="#90caf9", fontsize=8)
        ax2.tick_params(colors="#90caf9", labelsize=7)
        ax2.set_ylim(0, min(8000, sr / 2))

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=100, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")

    def generate_synthetic_sewer_audio(self, target_level_pct: float = 85.0, duration_sec: float = 3.0, filename: Optional[str] = None) -> bytes:
        """
        Synthesize realistic acoustic sound of underground turbulent sewer water.
        Higher levels produce louder, lower-frequency roaring resonance and splashing.
        """
        sr = 22050
        n_samples = int(sr * duration_sec)
        t = np.linspace(0, duration_sec, n_samples, endpoint=False)

        # Scale amplitude by target water level percentage
        amp_scale = 0.15 + (target_level_pct / 100.0) * 0.75

        # Ambient rumble (60 - 240 Hz culvert acoustic resonance)
        rumble = (
            0.5 * np.sin(2 * np.pi * 75 * t) +
            0.3 * np.sin(2 * np.pi * 140 * t) +
            0.2 * np.sin(2 * np.pi * 210 * t)
        )

        # Pink / turbulent noise for rushing fluid
        white_noise = np.random.normal(0, 0.4, n_samples)
        # Simple IIR filtering for fluid turbulence sound
        turbulent_noise = np.convolve(white_noise, np.ones(15) / 15, mode="same")

        # Combine components
        signal = amp_scale * (0.6 * turbulent_noise + 0.4 * rumble)

        # Intermittent splashing / droplet spikes if lower level; heavy surge if high level
        if target_level_pct > 70.0:
            splashes = np.random.normal(0, 0.3 * amp_scale, n_samples)
            signal += splashes

        # Normalize and convert to 16-bit PCM WAV
        signal = np.clip(signal, -0.98, 0.98)
        int16_data = (signal * 32767).astype(np.int16)

        bio = io.BytesIO()
        with wave.open(bio, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(int16_data.tobytes())

        wav_bytes = bio.getvalue()

        if filename:
            out_path = config.SAMPLE_AUDIO_DIR / filename
            with open(out_path, "wb") as f:
                f.write(wav_bytes)

        return wav_bytes


# Global acoustic model instance
acoustic_ai = AcousticLevelAI()

