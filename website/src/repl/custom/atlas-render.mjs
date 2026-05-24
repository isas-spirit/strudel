import { drawPianoroll } from '@strudel/draw';
import { renderPatternAudioBlob } from '@strudel/webaudio';

const LANE_PALETTE = ['#ff9f1c', '#2ec4b6', '#e71d36', '#6a4c93', '#4cc9f0', '#f72585', '#90be6d', '#f9c74f'];
const DEFAULT_WAV_OPTIONS = {
  begin: 0,
  end: 8,
  sampleRate: 48000,
  maxPolyphony: 1024,
  multiChannelOrbits: true,
  download: true,
  downloadName: undefined,
};
const DEFAULT_PIANOROLL_OPTIONS = {
  begin: 0,
  end: 8,
  width: 1600,
  height: 900,
  labels: 1,
  fold: 1,
  vertical: 0,
  playheadColor: '#ffffff',
  active: '#ffffff',
  inactive: '#94a3b8',
  background: '#0f1117',
  colorizeLanes: true,
  download: true,
  downloadName: undefined,
};

function requireCurrentMirror() {
  const mirror = window.strudelMirror;
  if (!mirror?.repl?.state?.pattern) {
    throw new Error('No active StrudelMirror pattern found. Evaluate code first.');
  }
  return mirror;
}

function getCurrentPatternContext() {
  const mirror = requireCurrentMirror();
  return {
    mirror,
    pattern: mirror.repl.state.pattern,
    cps: mirror.repl.scheduler.cps,
    code: mirror.code,
  };
}

function downloadBlob(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function canvasToBlob(canvas, type = 'image/png') {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (!blob) {
        reject(new Error('Canvas export failed')); 
        return;
      }
      resolve(blob);
    }, type);
  });
}

function laneKeyForHap(hap) {
  const value = hap?.value || {};
  if (value.label) return `label:${value.label}`;
  if (value.note) return `note:${value.note}`;
  if (value.s) return `sound:${value.s}`;
  if (value.n !== undefined) return `n:${value.n}`;
  return 'lane:default';
}

function colorizeHapsByLane(haps) {
  const laneMap = new Map();
  let idx = 0;
  for (const hap of haps) {
    hap.ensureObjectValue?.();
    const key = laneKeyForHap(hap);
    if (!laneMap.has(key)) {
      laneMap.set(key, LANE_PALETTE[idx % LANE_PALETTE.length]);
      idx += 1;
    }
    hap.value = { ...hap.value, color: hap.value?.color || laneMap.get(key) };
  }
  return Object.fromEntries(laneMap.entries());
}

function querySortedOnsets(pattern, cps, begin, end) {
  return pattern
    .queryArc(begin, end, { _cps: cps })
    .filter((hap) => hap.hasOnset())
    .sort((a, b) => a.whole.begin.valueOf() - b.whole.begin.valueOf());
}

function defaultName(prefix, ext, begin, end) {
  return `${prefix}-${begin}-${end}.${ext}`;
}

export async function atlasRenderPatternWav(pattern, cps, options = {}) {
  const opts = { ...DEFAULT_WAV_OPTIONS, ...options };
  const { blob } = await renderPatternAudioBlob(
    pattern,
    cps,
    opts.begin,
    opts.end,
    opts.sampleRate,
    opts.maxPolyphony,
    opts.multiChannelOrbits,
  );
  const fileName = opts.downloadName ? `${opts.downloadName}.wav` : defaultName('atlas-render', 'wav', opts.begin, opts.end);
  opts.download && downloadBlob(blob, fileName);
  return { blob, fileName, options: opts };
}

export async function atlasRenderCurrentWav(options = {}) {
  const { pattern, cps } = getCurrentPatternContext();
  return atlasRenderPatternWav(pattern, cps, options);
}

export function atlasRenderPatternPianorollCanvas(pattern, cps, options = {}) {
  const opts = { ...DEFAULT_PIANOROLL_OPTIONS, ...options };
  const canvas = document.createElement('canvas');
  canvas.width = opts.width;
  canvas.height = opts.height;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  const haps = querySortedOnsets(pattern, cps, opts.begin, opts.end);
  const laneColors = opts.colorizeLanes ? colorizeHapsByLane(haps) : {};
  drawPianoroll({
    ctx,
    time: opts.begin,
    haps,
    drawTime: [0, opts.end - opts.begin],
    labels: opts.labels,
    fold: opts.fold,
    vertical: opts.vertical,
    background: opts.background,
    active: opts.active,
    inactive: opts.inactive,
    playheadColor: opts.playheadColor,
  });
  return { canvas, ctx, haps, laneColors, options: opts };
}

export async function atlasRenderPatternPianoroll(options = {}) {
  const { pattern, cps } = getCurrentPatternContext();
  const rendered = atlasRenderPatternPianorollCanvas(pattern, cps, options);
  const blob = await canvasToBlob(rendered.canvas);
  const fileName = rendered.options.downloadName
    ? `${rendered.options.downloadName}.png`
    : defaultName('atlas-pianoroll', 'png', rendered.options.begin, rendered.options.end);
  rendered.options.download && downloadBlob(blob, fileName);
  return { ...rendered, blob, fileName };
}

export async function atlasRenderCurrentPianoroll(options = {}) {
  return atlasRenderPatternPianoroll(options);
}

export async function atlasRenderCurrentBundle(options = {}) {
  const wav = await atlasRenderCurrentWav(options.wav || options);
  const pianoroll = await atlasRenderCurrentPianoroll(options.pianoroll || options);
  return { wav, pianoroll };
}

export async function atlasCurrentPianorollDataUrl(options = {}) {
  const { pattern, cps } = getCurrentPatternContext();
  const rendered = atlasRenderPatternPianorollCanvas(pattern, cps, {
    ...options,
    download: false,
  });
  return rendered.canvas.toDataURL('image/png');
}

if (typeof window !== 'undefined') {
  window.atlasRender = {
    atlasRenderPatternWav,
    atlasRenderCurrentWav,
    atlasRenderPatternPianorollCanvas,
    atlasRenderPatternPianoroll,
    atlasRenderCurrentPianoroll,
    atlasRenderCurrentBundle,
    atlasCurrentPianorollDataUrl,
    getCurrentPatternContext,
  };
}
