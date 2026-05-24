#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable

import librosa
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Analyze a WAV/audio file and emit JSON + useful PNG aides.")
    p.add_argument("audio_path", help="Path to input audio file")
    p.add_argument("--outdir", help="Directory for analysis bundle outputs")
    p.add_argument("--stem", help="Output stem name (defaults to source filename stem)")
    p.add_argument("--sr", type=int, default=22050, help="Analysis sample rate")
    p.add_argument("--max-onsets", type=int, default=128, help="Maximum onset timestamps to include in JSON")
    p.add_argument("--timeseries-points", type=int, default=256, help="Maximum points for timeseries curves")
    return p.parse_args()


PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def downsample_series(times: np.ndarray, values: np.ndarray, max_points: int) -> list[dict]:
    if len(times) == 0:
        return []
    if len(times) <= max_points:
        idx = np.arange(len(times))
    else:
        idx = np.linspace(0, len(times) - 1, max_points).astype(int)
    return [{"t": round(float(times[i]), 4), "value": round(float(values[i]), 6)} for i in idx]


def norm01(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float32)
    if x.size == 0:
        return x
    lo = float(np.min(x))
    hi = float(np.max(x))
    if math.isclose(lo, hi):
        return np.zeros_like(x, dtype=np.float32)
    return (x - lo) / (hi - lo)


def db_norm(x: np.ndarray, top_db: float = 80.0) -> np.ndarray:
    y = librosa.power_to_db(np.maximum(x, 1e-12), ref=np.max)
    y = np.clip((y + top_db) / top_db, 0.0, 1.0)
    return y.astype(np.float32)


def colorize(img: np.ndarray) -> Image.Image:
    # simple dark-blue -> cyan -> yellow palette, robust without matplotlib
    x = np.clip(img, 0.0, 1.0)
    r = np.clip(255 * np.power(x, 0.85), 0, 255).astype(np.uint8)
    g = np.clip(255 * np.power(x, 1.3), 0, 255).astype(np.uint8)
    b = np.clip(255 * (0.18 + 0.82 * np.power(x, 2.2)), 0, 255).astype(np.uint8)
    rgb = np.dstack([r, g, b])
    return Image.fromarray(rgb, mode="RGB")


def save_matrix_png(matrix: np.ndarray, path: Path, flip_vertical: bool = True, width: int = 1400, height: int = 800) -> None:
    arr = np.asarray(matrix, dtype=np.float32)
    if flip_vertical:
        arr = np.flipud(arr)
    img = colorize(arr)
    img = img.resize((width, height), Image.Resampling.BICUBIC)
    img.save(path)


def save_curve_png(times: np.ndarray, values: np.ndarray, path: Path, width: int = 1400, height: int = 400, color=(255, 210, 64)) -> None:
    bg = Image.new("RGB", (width, height), (18, 20, 28))
    draw = ImageDraw.Draw(bg)
    draw.line((40, height - 30, width - 20, height - 30), fill=(80, 85, 98), width=1)
    draw.line((40, 20, 40, height - 30), fill=(80, 85, 98), width=1)
    if len(times) > 1:
        vals = norm01(values)
        t0 = float(times[0])
        t1 = float(times[-1]) if float(times[-1]) > t0 else t0 + 1.0
        pts = []
        for t, v in zip(times, vals):
            x = 40 + (float(t) - t0) / (t1 - t0) * (width - 60)
            y = (height - 30) - float(v) * (height - 60)
            pts.append((x, y))
        if len(pts) >= 2:
            draw.line(pts, fill=color, width=3)
    bg.save(path)


def estimate_key(chroma_mean: np.ndarray) -> str:
    if chroma_mean.size != 12:
        return "unknown"
    idx = int(np.argmax(chroma_mean))
    return PITCH_CLASSES[idx]


def onset_summary(onsets_s: np.ndarray, duration_s: float) -> dict:
    if len(onsets_s) < 2:
        return {"count": int(len(onsets_s)), "density_per_s": round(len(onsets_s) / max(duration_s, 1e-6), 4)}
    gaps = np.diff(onsets_s)
    return {
        "count": int(len(onsets_s)),
        "density_per_s": round(len(onsets_s) / max(duration_s, 1e-6), 4),
        "mean_gap_s": round(float(np.mean(gaps)), 4),
        "median_gap_s": round(float(np.median(gaps)), 4),
    }


def top_pitch_classes(chroma_mean: np.ndarray, k: int = 4) -> list[dict]:
    idxs = np.argsort(chroma_mean)[::-1][:k]
    return [{"pitch_class": PITCH_CLASSES[int(i)], "strength": round(float(chroma_mean[int(i)]), 6)} for i in idxs]


def analyze(audio_path: Path, sr: int, max_onsets: int, timeseries_points: int) -> tuple[dict, dict[str, np.ndarray]]:
    y, sr = librosa.load(str(audio_path), sr=sr, mono=True)
    duration_s = len(y) / sr
    peak = float(np.max(np.abs(y))) if len(y) else 0.0
    clipped_samples = int(np.sum(np.abs(y) >= 0.999)) if len(y) else 0

    # adapt FFT sizes for short one-shots so analysis stays useful without warnings
    n_fft = min(2048, max(256, 2 ** int(math.floor(math.log2(max(len(y), 256))))))
    hop_length = max(64, n_fft // 4)

    rms = librosa.feature.rms(y=y, frame_length=n_fft, hop_length=hop_length)[0]
    rms_times = librosa.times_like(rms, sr=sr, hop_length=hop_length)

    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
    onset_times = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=hop_length, units="time")
    onset_env_times = librosa.times_like(onset_env, sr=sr, hop_length=hop_length)

    tempo_raw, beat_frames = librosa.beat.beat_track(y=y, sr=sr, onset_envelope=onset_env, hop_length=hop_length)
    tempo_bpm = float(np.ravel(np.asarray(tempo_raw))[0]) if np.size(tempo_raw) else 0.0
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop_length)

    centroid = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=n_fft, hop_length=hop_length)[0]
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, n_fft=n_fft, hop_length=hop_length)[0]
    flatness = librosa.feature.spectral_flatness(y=y, n_fft=n_fft, hop_length=hop_length)[0]
    zcr = librosa.feature.zero_crossing_rate(y, frame_length=n_fft, hop_length=hop_length)[0]
    centroid_times = librosa.times_like(centroid, sr=sr, hop_length=hop_length)

    chroma = librosa.feature.chroma_stft(y=y, sr=sr, n_fft=n_fft, hop_length=hop_length)
    chroma_mean = np.mean(chroma, axis=1) if chroma.size else np.zeros(12, dtype=np.float32)

    y_h, y_p = librosa.effects.hpss(y)
    harmonic_energy = float(np.mean(np.square(y_h))) if len(y_h) else 0.0
    percussive_energy = float(np.mean(np.square(y_p))) if len(y_p) else 0.0
    total_hp = harmonic_energy + percussive_energy

    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=n_fft, hop_length=hop_length, n_mels=128, fmax=sr // 2)
    stft_mag = np.abs(librosa.stft(y=y, n_fft=n_fft, hop_length=hop_length))
    tempogram = librosa.feature.tempogram(onset_envelope=onset_env, sr=sr, hop_length=hop_length)

    meta = {
        "source": str(audio_path),
        "analysis_sample_rate": int(sr),
        "duration_s": round(float(duration_s), 4),
        "peak_abs": round(peak, 6),
        "clipped_samples": clipped_samples,
        "rms_mean": round(float(np.mean(rms)) if len(rms) else 0.0, 6),
        "tempo_bpm_est": round(tempo_bpm, 3),
        "beat_count": int(len(beat_times)),
        "onsets": [round(float(t), 4) for t in onset_times[:max_onsets]],
        "onset_summary": onset_summary(onset_times, duration_s),
        "spectral_centroid_mean": round(float(np.mean(centroid)) if len(centroid) else 0.0, 4),
        "spectral_rolloff_mean": round(float(np.mean(rolloff)) if len(rolloff) else 0.0, 4),
        "spectral_flatness_mean": round(float(np.mean(flatness)) if len(flatness) else 0.0, 6),
        "zero_crossing_rate_mean": round(float(np.mean(zcr)) if len(zcr) else 0.0, 6),
        "key_center_guess": estimate_key(chroma_mean),
        "top_pitch_classes": top_pitch_classes(chroma_mean),
        "harmonic_energy_ratio": round(harmonic_energy / total_hp, 6) if total_hp > 0 else 0.0,
        "percussive_energy_ratio": round(percussive_energy / total_hp, 6) if total_hp > 0 else 0.0,
        "curves": {
            "rms": downsample_series(rms_times, rms, timeseries_points),
            "onset_strength": downsample_series(onset_env_times, onset_env, timeseries_points),
            "spectral_centroid": downsample_series(centroid_times, centroid, timeseries_points),
        },
    }

    visuals = {
        "mel": db_norm(mel),
        "spectrogram": db_norm(stft_mag**2),
        "chroma": norm01(chroma),
        "tempogram": norm01(tempogram),
        "rms_times": rms_times,
        "rms": rms,
        "onset_times": onset_env_times,
        "onset_env": onset_env,
        "centroid_times": centroid_times,
        "centroid": centroid,
    }
    return meta, visuals


def write_bundle(outdir: Path, stem: str, meta: dict, visuals: dict[str, np.ndarray]) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "json": outdir / f"{stem}.analysis.json",
        "mel": outdir / f"{stem}.mel.png",
        "spectrogram": outdir / f"{stem}.spectrogram.png",
        "chroma": outdir / f"{stem}.chroma.png",
        "tempogram": outdir / f"{stem}.tempogram.png",
        "rms": outdir / f"{stem}.rms.png",
        "onset_strength": outdir / f"{stem}.onset_strength.png",
        "centroid": outdir / f"{stem}.centroid.png",
    }
    outputs["json"].write_text(json.dumps(meta, indent=2), encoding="utf-8")
    save_matrix_png(visuals["mel"], outputs["mel"])
    save_matrix_png(visuals["spectrogram"], outputs["spectrogram"])
    save_matrix_png(visuals["chroma"], outputs["chroma"], width=1400, height=300)
    save_matrix_png(visuals["tempogram"], outputs["tempogram"], width=1400, height=300)
    save_curve_png(visuals["rms_times"], visuals["rms"], outputs["rms"], color=(255, 210, 64))
    save_curve_png(visuals["onset_times"], visuals["onset_env"], outputs["onset_strength"], color=(96, 220, 255))
    save_curve_png(visuals["centroid_times"], visuals["centroid"], outputs["centroid"], color=(255, 128, 192))
    return {k: str(v) for k, v in outputs.items()}


def main() -> None:
    args = parse_args()
    audio_path = Path(args.audio_path).expanduser().resolve()
    if not audio_path.exists():
        raise SystemExit(f"Input file not found: {audio_path}")
    outdir = Path(args.outdir).expanduser().resolve() if args.outdir else audio_path.parent / f"{audio_path.stem}.analysis"
    stem = args.stem or audio_path.stem
    meta, visuals = analyze(audio_path, args.sr, args.max_onsets, args.timeseries_points)
    files = write_bundle(outdir, stem, meta, visuals)
    result = {
        "ok": True,
        "source": str(audio_path),
        "outdir": str(outdir),
        "files": files,
        "summary": {
            "duration_s": meta["duration_s"],
            "tempo_bpm_est": meta["tempo_bpm_est"],
            "key_center_guess": meta["key_center_guess"],
            "onset_count": meta["onset_summary"]["count"],
            "harmonic_energy_ratio": meta["harmonic_energy_ratio"],
            "percussive_energy_ratio": meta["percussive_energy_ratio"],
        },
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
