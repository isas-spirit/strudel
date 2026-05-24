#!/usr/bin/env python3
from __future__ import annotations

import math
import random
import wave
from pathlib import Path

SAMPLE_RATE = 44100
ROOT = Path(__file__).resolve().parents[1] / 'website' / 'public' / 'user-samples' / 'atlas-foundation'
PERC = ROOT / 'percussion'
TEXT = ROOT / 'textures'

random.seed(24)


def ensure_dirs() -> None:
    PERC.mkdir(parents=True, exist_ok=True)
    TEXT.mkdir(parents=True, exist_ok=True)


def clamp(x: float) -> float:
    return max(-1.0, min(1.0, x))


def write_wav(path: Path, frames: list[float]) -> None:
    with wave.open(str(path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        pcm = bytearray()
        for sample in frames:
            value = int(clamp(sample) * 32767)
            pcm += value.to_bytes(2, 'little', signed=True)
        wf.writeframes(bytes(pcm))


def env_exp(i: int, total: int, start: float = 1.0, end: float = 1e-4) -> float:
    if total <= 1:
        return end
    t = i / (total - 1)
    return start * ((end / start) ** t)


def kick(length_s: float, base_freq: float, drop: float) -> list[float]:
    total = int(SAMPLE_RATE * length_s)
    out: list[float] = []
    phase = 0.0
    for i in range(total):
        t = i / SAMPLE_RATE
        amp = env_exp(i, total, 1.0, 1e-5)
        freq = base_freq + drop * math.exp(-t * 18)
        phase += (2 * math.pi * freq) / SAMPLE_RATE
        body = math.sin(phase)
        click = (1.0 - min(1.0, t * 220)) * (random.random() * 2 - 1) * 0.18
        out.append((body * amp * 0.92) + click)
    return out


def snare(length_s: float, tone_freq: float) -> list[float]:
    total = int(SAMPLE_RATE * length_s)
    out: list[float] = []
    phase = 0.0
    for i in range(total):
        t = i / SAMPLE_RATE
        tone_env = env_exp(i, total, 1.0, 1e-4)
        noise_env = math.exp(-t * 18)
        phase += (2 * math.pi * tone_freq) / SAMPLE_RATE
        tone = math.sin(phase) * tone_env * 0.35
        noise = (random.random() * 2 - 1) * noise_env * 0.8
        out.append(tone + noise)
    return out


def hat(length_s: float, brightness: float) -> list[float]:
    total = int(SAMPLE_RATE * length_s)
    out: list[float] = []
    phase_a = phase_b = phase_c = 0.0
    for i in range(total):
        t = i / SAMPLE_RATE
        amp = math.exp(-t * brightness)
        phase_a += (2 * math.pi * 4100) / SAMPLE_RATE
        phase_b += (2 * math.pi * 6200) / SAMPLE_RATE
        phase_c += (2 * math.pi * 9300) / SAMPLE_RATE
        metal = (math.sin(phase_a) + math.sin(phase_b) * 0.7 + math.sin(phase_c) * 0.45) * 0.22
        noise = (random.random() * 2 - 1) * 0.45
        out.append((metal + noise) * amp)
    return out


def texture(length_s: float, freq_a: float, freq_b: float) -> list[float]:
    total = int(SAMPLE_RATE * length_s)
    out: list[float] = []
    phase_a = phase_b = lfo = 0.0
    for i in range(total):
        t = i / SAMPLE_RATE
        fade_in = min(1.0, t / 0.2)
        fade_out = min(1.0, (length_s - t) / 0.4)
        amp = max(0.0, min(fade_in, fade_out)) * 0.6
        phase_a += (2 * math.pi * freq_a) / SAMPLE_RATE
        phase_b += (2 * math.pi * freq_b) / SAMPLE_RATE
        lfo += (2 * math.pi * 0.27) / SAMPLE_RATE
        drift = math.sin(lfo) * 0.08
        noise = (random.random() * 2 - 1) * 0.03
        sample = math.sin(phase_a + drift) * 0.55 + math.sin(phase_b - drift) * 0.45 + noise
        out.append(sample * amp)
    return out


def main() -> None:
    ensure_dirs()
    write_wav(PERC / 'ak_00.wav', kick(0.55, 46, 130))
    write_wav(PERC / 'ak_01.wav', kick(0.42, 54, 170))
    write_wav(PERC / 'as_00.wav', snare(0.28, 190))
    write_wav(PERC / 'as_01.wav', snare(0.22, 240))
    write_wav(PERC / 'ah_00.wav', hat(0.08, 52))
    write_wav(PERC / 'ah_01.wav', hat(0.12, 38))
    write_wav(PERC / 'ah_02.wav', hat(0.04, 80))
    write_wav(TEXT / 'atx_00.wav', texture(1.8, 110, 164.5))
    write_wav(TEXT / 'atx_01.wav', texture(2.4, 82.4, 123.5))


if __name__ == '__main__':
    main()
