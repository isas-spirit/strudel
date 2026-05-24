# Co-Creation Foundation Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build the first durable co-creation layer on top of the hosted Strudel site so Vincent and Hermes can collaboratively create custom functions, custom sample packs, and reusable musical sketches.

**Architecture:** Keep upstream Strudel mostly intact and add a thin site-specific layer under `website/src/repl/custom/` plus same-origin sample assets under `website/public/user-samples/`. Wire both into the website REPL boot path via `website/src/repl/util.mjs` and `website/src/repl/prebake.mjs`.

**Tech Stack:** Strudel website REPL, Astro, React, Strudel evalScope, Strudel webaudio samples loader, Python WAV generation.

---

## Task 1: Scaffold custom runtime module layout

**Objective:** Create clear homes for Hermes/Vincent-specific runtime code.

**Files:**
- Create: `website/src/repl/custom/index.mjs`
- Create: `website/src/repl/custom/atlas-functions.mjs`
- Create: `website/src/repl/custom/atlas-patterns.mjs`
- Create: `website/src/repl/custom/atlas-sample-library.mjs`

**Implementation notes:**
- `atlas-functions.mjs` should export top-level helpers.
- `atlas-patterns.mjs` should attach `Pattern.prototype` methods.
- `atlas-sample-library.mjs` should centralize sample-pack URLs and preload helpers.
- `index.mjs` should re-export the stable public surface.

**Verification:**
- files exist
- imports resolve from `website/src/repl/custom/index.mjs`

---

## Task 2: Wire custom runtime into REPL scope

**Objective:** Make custom helpers available inside live Strudel evaluation.

**Files:**
- Modify: `website/src/repl/util.mjs`
- Modify: `website/src/repl/prebake.mjs`

**Implementation notes:**
- add the custom module to `loadModules()` via `evalScope(...)`
- import `atlas-patterns.mjs` in prebake path so prototype extensions load on boot
- keep the integration thin and isolated

**Verification:**
- website build succeeds
- exported helper names become reachable in eval scope

---

## Task 3: Add first co-creation helper functions

**Objective:** Provide immediately useful primitives for collaborative composition without deep engine surgery.

**Files:**
- Modify: `website/src/repl/custom/atlas-functions.mjs`
- Modify: `website/src/repl/custom/atlas-patterns.mjs`

**Implementation notes:**
- include a few safe starter helpers, e.g.:
  - sketch metadata helper / comment template support
  - sample-pack helper loader
  - a simple chainable timing/velocity/style helper
- do not overdesign; make these clearly examples and foundation pieces

**Verification:**
- helpers compile
- helpers can be called from REPL code without runtime errors

---

## Task 4: Create same-origin sample-pack foundation

**Objective:** Add a deployable custom sample library root for Hermes-generated sounds.

**Files:**
- Create: `website/public/user-samples/atlas-foundation/strudel.json`
- Create: `website/public/user-samples/atlas-foundation/percussion/*.wav`
- Create: `website/public/user-samples/atlas-foundation/textures/*.wav`
- Create: `tools/generate_atlas_foundation_samples.py`

**Implementation notes:**
- generate a tiny but real sample set with Python
- keep naming stable and easy to compose with
- manifest should rely on manifest-relative paths where possible

**Verification:**
- files exist in `website/public`
- manifest shape is valid for Strudel `samples(...)`

---

## Task 5: Preload the custom sample pack

**Objective:** Make the custom sample library available automatically in the hosted REPL.

**Files:**
- Modify: `website/src/repl/prebake.mjs`

**Implementation notes:**
- preload via same-origin manifest URL under `/tools/music-lab/...`
- tag it as user/custom if supported
- keep load order explicit

**Verification:**
- website build succeeds
- manifest URL is referenced in prebake

---

## Task 6: Add co-creation documentation

**Objective:** Document how Vincent and Hermes should use the new layer.

**Files:**
- Create: `docs/CO-CREATION-LAYER.md`
- Possibly update: `docs/CUSTOMIZING-STRUDEL.md`

**Implementation notes:**
- explain where to add new functions
- explain how to add/generate samples
- explain the recommended workflow for collaborative track creation

**Verification:**
- docs mention exact file paths
- docs match actual scaffolded files

---

## Task 7: Add one end-to-end demo sketch

**Objective:** Prove the whole pipeline works conceptually.

**Files:**
- Create or modify: `website/src/repl/tunes.mjs`

**Implementation notes:**
- add one stock/demo sketch that uses:
  - at least one custom helper
  - at least one custom atlas sample
- keep it small and obviously demonstrative

**Verification:**
- website build succeeds
- demo code is valid Strudel code

---

## Task 8: Verify and commit

**Objective:** Confirm the foundation is healthy and save it cleanly.

**Files:**
- Modify: any touched files above

**Commands:**
```bash
cd /home/isa/tools/music-lab-strudel/strudel-upstream
pnpm --filter @strudel/website build
```

**Expected:**
- build completes successfully

**Commit target:**
```bash
git add docs/plans/2026-05-24-co-creation-foundation.md docs/CO-CREATION-LAYER.md website/src/repl/custom website/src/repl/util.mjs website/src/repl/prebake.mjs website/public/user-samples tools/generate_atlas_foundation_samples.py website/src/repl/tunes.mjs
git commit -m "feat: scaffold strudel co-creation foundation"
```
