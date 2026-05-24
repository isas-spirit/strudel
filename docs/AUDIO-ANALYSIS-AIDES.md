# Audio Analysis Aides for Hermes/Strudel Co-Creation

This note focuses on the problem that Hermes cannot directly hear audio, so we need analysis aids that make rendered music legible to an LLM.

## Goal

Build a pipeline that lets Hermes reason about:
- rendered tracks from Strudel code
- one-shot / loop samples
- changes over time
- relationships between code, visuals, and user feedback

We want a small number of high-value analysis views, not every possible chart all the time.

## Current implementation status

Implemented now:
- `tools/analyze_audio.py`
  - takes an audio file
  - emits an analysis bundle with JSON + PNG aides
  - currently writes:
    - `*.analysis.json`
    - `*.mel.png`
    - `*.spectrogram.png`
    - `*.chroma.png`
    - `*.tempogram.png`
    - `*.rms.png`
    - `*.onset_strength.png`
    - `*.centroid.png`

Still missing:
- programmatic Strudel code-to-WAV export for Hermes automation
- pianoroll PNG export pipeline
- higher-level orchestration wrapper for code-or-WAV analysis jobs

---

## Grounded current capabilities

### 1. WAV export from Strudel code: yes, already exists

Current live REPL has an export flow:
- `website/src/repl/components/panel/ExportTab.jsx`
- `website/src/repl/useReplContext.jsx`
- `packages/webaudio/webaudio.mjs`

Grounding:
- `ExportTab.jsx` exposes an **Export to WAV** UI with:
  - file name
  - start cycle
  - end cycle
  - sample rate
  - max polyphony
  - multi-channel orbits
- `useReplContext.jsx` calls `handleExport(...)`
- `packages/webaudio/webaudio.mjs` has `renderPatternAudio(...)`
- `renderPatternAudio(...)` builds an `OfflineAudioContext`, renders the pattern, converts the buffer to WAV, and triggers a download

So: **code -> rendered WAV** is already real.

### 2. Pianoroll visualization: yes, already exists

Grounding:
- `packages/draw/pianoroll.mjs`
- docs mention both `.pianoroll()` and `._pianoroll()`

Important details:
- `.pianoroll()` draws into the editor background
- `._pianoroll()` puts the pianoroll visually under a pattern
- `drawPianoroll(...)` and `__pianoroll(...)` are exported functions
- the renderer already uses event colors if present:
  - it reads `event.value?.color`

This means **color-coded lanes/tracks are already conceptually supported** if the pattern events are given distinct colors.

### 3. Image feedback into Hermes: yes

Grounding in Hermes docs:
- `vision_analyze` can analyze images
- `browser_vision` can take and analyze screenshots
- screenshots can be shared back into chat via `MEDIA:`

So if we produce an image file locally, Hermes can inspect it with:
- `vision_analyze(image_url=<local file path>, question=...)`

And if useful for discussion, that image can be posted into Telegram using:
- `MEDIA:/absolute/path/to/file.png`

### 4. Classical audio analysis on WAVs: very feasible

Local environment currently has:
- `librosa`
- `numpy`
- `scipy`
- `soundfile`

So a Python-based audio-analysis toolchain is easy to build.

---

## Current gaps

### Gap A: programmatic WAV export for Hermes tools

Current Strudel export path is browser-first and download-oriented.

`renderPatternAudio(...)` currently:
- renders offline audio
- turns it into a Blob
- clicks a download link

That is good for humans, but not yet ideal for Hermes automation.

### Recommended fix
Create a new utility path that can:
- render a pattern
- return a WAV buffer / blob / file path
- skip browser-download behavior

Best shape:
- keep existing export UX unchanged
- add a second function for automation, something like:
  - `renderPatternAudioToBlob(...)`
  - `renderPatternAudioToWavBuffer(...)`
  - or site-level wrapper that saves to a file

---

### Gap B: no first-class image export for pianoroll yet

Pianoroll drawing exists, but there is no current dedicated "export this visual as PNG" flow.

### Recommended fix
Add a small helper that:
1. creates a dedicated canvas
2. calls `drawPianoroll(...)` or `__pianoroll(...)`
3. exports PNG via canvas APIs
4. returns / saves the image file

This is very doable.

---

## Recommended analysis tracks

## Track 1: Classical metadata analysis

This is the low-friction, high-utility layer.

### Good metadata outputs

For full tracks / rendered sections:
- duration
- sample rate
- integrated loudness / RMS envelope
- peak level / clipping detection
- onset times
- estimated tempo / beat grid confidence
- spectral centroid / brightness trend
- spectral rolloff
- spectral flux
- chroma summary
- key / tonal center guess
- harmonic vs percussive energy ratio
- section-change hints / novelty curve

For samples / one-shots:
- duration
- peak and RMS
- zero-crossing rate
- spectral centroid / rolloff
- transient sharpness
- pitch estimate if tonal
- noisiness / harmonicity estimate
- rough category hints:
  - kick / snare / hat / texture / drone / tonal stab / fx

### Most useful with timestamps
For tracks, time-indexed views matter most:
- onset list with times
- loudness over time
- novelty / change points
- chroma over time
- tempogram / pulse confidence over time

### Best use cases
Use classical metadata when:
- you want quick structural understanding
- you want to compare two renders
- you want to detect timing density / brightness / energy changes
- you want to classify samples
- you want machine-readable summaries for agent logic

### Recommendation
Build a small local analysis CLI/tool that outputs JSON like:

```json
{
  "duration_s": 16.0,
  "tempo_bpm_est": 104.2,
  "onsets": [{"t": 0.12}, {"t": 0.51}],
  "sections": [{"start": 0.0, "end": 4.0, "label": "intro"}],
  "loudness_curve": [...],
  "brightness_curve": [...],
  "key_estimate": "A minor"
}
```

That gives Hermes a symbolic foothold.

---

## Track 2: Visual analysis

This is the more powerful but more selective layer.

The goal is not just pretty pictures. It is to produce images that an LLM can reason over.

## Highest-value visual types

### A. Pianoroll / event-lane image

Best for:
- code-to-music alignment
- discussing note placement
- talking about rhythm lanes by color
- multi-part structure

Especially strong if we:
- render each musical layer in a different color
- keep stable color semantics
- optionally annotate lane names

This is probably the **single most valuable visual bridge** between you, the code, and Hermes.

### B. Spectrogram / mel spectrogram

Best for:
- timbral density
- bass vs highs balance
- transient density
- noise vs tonal material
- comparing before/after sound design changes

Good general-purpose audio image.

### C. HPSS view (harmonic/percussive split)

Best for:
- separating drums from sustained tonal material
- understanding whether a texture is mostly tonal or noisy/percussive

Useful when arrangements get dense.

### D. Chroma / pitch-class heatmap

Best for:
- tonal center
- chord drift
- pitch-class emphasis
- harmonic comparison between renders

Useful mostly on melodic/harmonic sections, not pure percussion.

### E. Tempogram / onset-strength / novelty curve

Best for:
- groove density
- pulse ambiguity
- change detection
- section boundary hints

Useful when Hermes needs to answer questions like:
- where does the groove open up?
- where does the drop hit?
- which section is densest?

### F. Loudness envelope image

Best for:
- macro dynamics
- transition shaping
- level balancing across sections

Simple, cheap, useful.

---

## Recommended visualization policy

Do **not** render everything every time.

### Default views for full track render
1. metadata JSON
2. mel spectrogram
3. loudness/onset/tempo composite
4. pianoroll if the code is pattern-heavy and note/rhythm structure matters

### Default views for sample analysis
1. waveform + envelope
2. spectrogram
3. compact metadata JSON

### Pull these only when needed
- chroma
- MFCC
- HPSS
- self-similarity
- novelty matrices

These are powerful, but not always worth the cost/noise.

---

## Pianoroll-specific recommendations

### Color-coded lanes
This is worth doing.

The current pianoroll renderer already reads `event.value?.color`, so we should exploit that.

Recommended convention:
- drums: one stable palette
- bass: one stable palette
- tonal lead: one stable palette
- textures/pads: one stable palette
- fx/transitions: one stable palette

Then you can say things like:
- "thin out the orange lane in bars 9-16"
- "mirror the green lane rhythm onto the purple lane"

That is exactly the kind of multimodal shared reference we want.

### What to add
A dedicated render helper should support:
- fixed width/height
- time window selection
- optional fold/no-fold mode
- optional labels
- optional lane legend
- transparent vs dark background
- stable color themes

---

## Suggested pipeline architecture

## Stage 1 — render source

### For Strudel code
- render WAV from code section
- optionally render pianoroll PNG from same section

### For samples
- use existing WAV directly
- optionally generate spectrogram PNG immediately

## Stage 2 — derive machine-readable analysis

Python tool outputs:
- JSON metadata
- optional CSV time series

## Stage 3 — derive image views

Image outputs based on use case:
- pianoroll
- mel spectrogram
- waveform/loudness
- chroma
- tempogram

## Stage 4 — Hermes consumption

Hermes can then use:
- JSON directly for symbolic reasoning
- `vision_analyze` on selected images
- `MEDIA:` to share images back into Telegram for discussion

---

## Practical implementation slices

### Slice A: audio-analysis tool
Build first.

Create something like:
- `tools/analyze_audio.py`

Inputs:
- WAV path

Outputs:
- JSON summary
- optional PNGs

This is the easiest, most obviously valuable piece.

### Slice B: pianoroll export helper
Build second.

Create a site/runtime utility that can:
- evaluate or query a pattern span
- draw a pianoroll to canvas
- export PNG

### Slice C: Hermes-facing orchestration
Build third.

Eventually add a small analysis harness that given either:
- Strudel code + time span
- or WAV path

produces:
- render
- metadata
- selected images
- paths Hermes can inspect

---

## Best analysis views by situation

### When editing arrangement / rhythm
Use:
- pianoroll
- onset/loudness curve
- tempogram

### When editing timbre / sound design
Use:
- spectrogram
- HPSS
- sample metadata

### When editing harmony / pitch
Use:
- pianoroll
- chroma
- note/event metadata if available

### When editing transitions / macro shape
Use:
- loudness envelope
- novelty/change curve
- wide spectrogram

### When evaluating individual samples
Use:
- waveform/envelope
- short spectrogram
- transient + pitch metadata

---

## Telegram / chat integration

For Hermes discussion loops:
- images can be analyzed locally with `vision_analyze`
- images can be posted into Telegram using `MEDIA:/absolute/path.png`
- browser screenshots can also be analyzed/shared via `browser_vision` and `MEDIA:`

So yes: once we produce PNGs locally, they are easy to:
1. inspect as agent inputs
2. send back to you in chat

---

## Strong recommendation

Build this in this order:

1. **audio metadata tool**
2. **spectrogram / compact visualization exporter**
3. **pianoroll PNG exporter with color lanes**
4. **Hermes orchestration wrapper for code-or-WAV analysis**

That gives fast value without overbuilding.

---

## Proposed next concrete tasks

1. create `tools/analyze_audio.py`
   - JSON metadata
   - optional spectrogram/loudness plots
2. create `website/src/repl/custom/atlas-analysis.mjs` or similar
   - helpers / conventions for analysis-oriented rendering
3. add a dedicated pianoroll export utility
4. define a small "analysis bundle" convention:
   - `track.wav`
   - `track.analysis.json`
   - `track.spectrogram.png`
   - `track.pianoroll.png`

That would be a strong first version of the listening prosthetics Hermes needs.
