# Co-Creation Layer

This file documents the first site-specific layer for collaborative music-making between Vincent and Hermes.

## Purpose

We want three things:

1. a safe place for custom Strudel helpers
2. a safe place for custom pattern methods
3. a same-origin sample library for Hermes-generated sounds

The design goal is to keep upstream Strudel mostly intact while giving us a durable extension surface.

---

## File map

### Runtime helpers
- `website/src/repl/custom/atlas-functions.mjs`
- `website/src/repl/custom/atlas-patterns.mjs`
- `website/src/repl/custom/atlas-sample-library.mjs`
- `website/src/repl/custom/atlas-render.mjs`
- `website/src/repl/custom/index.mjs`

### Runtime wiring
- `website/src/repl/util.mjs`
- `website/src/repl/prebake.mjs`

### Sample assets
- `website/public/user-samples/atlas-foundation/`
- `website/public/user-samples/atlas-foundation/strudel.json`

### Sample generation
- `tools/generate_atlas_foundation_samples.py`

---

## How to add new custom functions

Put exported helpers in:
- `website/src/repl/custom/atlas-functions.mjs`

These are loaded into the REPL scope through:
- `website/src/repl/util.mjs`

If a helper should be callable directly inside Strudel code, export it from `atlas-functions.mjs` and re-export it from `custom/index.mjs`.

### Current starter helpers
- `atlasSamples(pack?, version?)`
- `atlasDrums(pattern?)`
- `atlasTexture(pattern?, gainAmount?)`
- `atlasSketch(drums?, texture?)`

These are intentionally simple. They are foundation pieces, not final musical language.

---

## How to add new chain methods

Put `Pattern.prototype` extensions in:
- `website/src/repl/custom/atlas-patterns.mjs`

These load on REPL boot via:
- `website/src/repl/prebake.mjs`
- `website/src/repl/custom/index.mjs`

### Current starter methods
- `.atlasSwing(subdivision?, amount?)`
- `.atlasGhosts(offset?, ghostGain?)`
- `.atlasTight(release?, end?)`

These should stay musically useful and small.

---

## How to add new sample packs

### Foundation pack path
- `website/public/user-samples/atlas-foundation/`

### Manifest
- `website/public/user-samples/atlas-foundation/strudel.json`

The site loads it same-origin, so samples can be fetched with:

```js
atlasSamples()
```

which currently resolves to `/tools/music-lab/user-samples/atlas-foundation/strudel.json?...`

### Recommended pack structure

```text
website/public/user-samples/
  atlas-foundation/
    strudel.json
    percussion/
    textures/
```

For future packs, keep one pack per directory.

---

## How to generate sounds with Hermes

Default workflow:

1. decide aesthetic / role
2. generate WAVs with Python
3. place them in `website/public/user-samples/<pack>/...`
4. update `strudel.json`
5. preload or manually load the pack
6. write Strudel sketches that use it

The starter generator is:
- `tools/generate_atlas_foundation_samples.py`

It currently creates a small pack with:
- `ak` kicks
- `as` snares
- `ah` hats
- `atx` textures

---

## How to use the current foundation in code

Example:

```js
atlasSamples()
stack(
  atlasDrums("ak ah as ah").atlasSwing(4, 1/3),
  atlasTexture("atx").gain(0.25)
)
```

Or:

```js
atlasSketch("ak*2 ah*8 as", "atx")
```

---

## Rules for future work

Prefer this order:

1. add a helper function
2. add a chain method if syntax clearly wants it
3. add a deeper control/runtime feature only when needed
4. avoid parser / mini-notation changes unless truly necessary

Keep this layer small, legible, and site-specific.
