# Render Pipeline for Hermes / Strudel Co-Creation

This note describes the first automation-friendly render helpers added on top of the live Strudel site.

## Why this exists

We need a bridge from:
- Strudel code
- to rendered WAV
- to rendered structural visuals
- to analysis artifacts Hermes can inspect

The immediate goal is not full automation yet. The immediate goal is to expose stable render primitives that both humans and Hermes can call.

---

## Current primitives

### Browser/runtime-side render helpers

File:
- `website/src/repl/custom/atlas-render.mjs`

Loaded via:
- `website/src/repl/custom/index.mjs`
- `website/src/repl/util.mjs`

Available in REPL/global scope and also on `window.atlasRender`.

### WAV helpers
- `atlasRenderPatternWav(pattern, cps, options)`
- `atlasRenderCurrentWav(options)`

These use:
- `packages/webaudio/webaudio.mjs`
- new helper: `renderPatternAudioBlob(...)`

### Pianoroll helpers
- `atlasRenderPatternPianorollCanvas(pattern, cps, options)`
- `atlasRenderPatternPianoroll(options)`
- `atlasRenderCurrentPianoroll(options)`
- `atlasCurrentPianorollDataUrl(options)`

These use:
- `packages/draw/pianoroll.mjs`
- `drawPianoroll(...)`

### Combined helper
- `atlasRenderCurrentBundle(options)`

This currently renders:
- WAV
- pianoroll PNG

as two separate export steps.

---

## Current behavior

### For current REPL state
`atlasRenderCurrentWav(...)` and related helpers inspect:
- `window.strudelMirror.repl.state.pattern`
- `window.strudelMirror.repl.scheduler.cps`

So they operate on the **currently evaluated pattern**.

That means:
1. evaluate the code first
2. call the helper

---

## Example usage

### Export WAV for current pattern
```js
await atlasRenderCurrentWav({
  begin: 0,
  end: 16,
  sampleRate: 48000,
  downloadName: 'my-track',
})
```

### Export pianoroll PNG for current pattern
```js
await atlasRenderCurrentPianoroll({
  begin: 0,
  end: 16,
  width: 1800,
  height: 900,
  labels: 1,
  fold: 1,
  downloadName: 'my-track-pianoroll',
})
```

### Export both
```js
await atlasRenderCurrentBundle({
  wav: {
    begin: 0,
    end: 16,
    downloadName: 'my-track'
  },
  pianoroll: {
    begin: 0,
    end: 16,
    width: 1800,
    height: 900,
    downloadName: 'my-track-pianoroll'
  }
})
```

### Get pianoroll as data URL instead of download
```js
const pngDataUrl = await atlasCurrentPianorollDataUrl({
  begin: 0,
  end: 8,
  width: 1600,
  height: 800,
})
```

This is especially relevant for future Hermes/browser automation.

---

## Lane coloring

Pianoroll export includes a first lane-coloring pass.

Current strategy:
- infer lane identity from event fields like:
  - `label`
  - `note`
  - `s`
  - `n`
- assign stable colors from a palette
- write those colors into `hap.value.color`
- `drawPianoroll(...)` already respects that color

This is the first step toward discussions like:
- "thin out the orange lane"
- "double the purple lane in bars 9-16"

It is intentionally simple right now and can be made more musical later.

---

## Current limitations

### WAV export
The helper now returns a Blob-capable render path via `renderPatternAudioBlob(...)`, but the site helpers still primarily think in browser/download terms.

### Pianoroll export
The PNG export works at the browser runtime layer, but we do not yet have:
- a persistent file-save path outside browser download behavior
- a direct Hermes-local file emission path

### Full analysis pipeline
We now have:
- render helpers
- `tools/analyze_audio.py`

But they are not yet fully connected into one-button orchestration.

---

## Next recommended steps

1. add a higher-level browser helper that exports a named artifact bundle consistently
2. add a lightweight orchestration path from render output to `analyze_audio.py`
3. add a more semantic lane-mapping system for pianoroll colors
4. optionally add a non-download persistence path if we need Hermes to capture artifacts automatically rather than via browser downloads

---

## Related files

- `packages/webaudio/webaudio.mjs`
- `packages/draw/pianoroll.mjs`
- `website/src/repl/custom/atlas-render.mjs`
- `docs/AUDIO-ANALYSIS-AIDES.md`
- `tools/analyze_audio.py`
