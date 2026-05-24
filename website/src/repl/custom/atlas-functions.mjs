import { s, stack } from '@strudel/core';
import { loadAtlasPack, preloadAtlasFoundation, ATLAS_FOUNDATION_PACK } from './atlas-sample-library.mjs';

export { loadAtlasPack as atlasSamples, preloadAtlasFoundation, ATLAS_FOUNDATION_PACK };

export function atlasDrums(pattern = 'ak ah as ah') {
  return s(pattern);
}

export function atlasTexture(pattern = 'atx', gainAmount = 0.35) {
  return s(pattern).slow(4).gain(gainAmount).room(0.6);
}

export function atlasSketch(drums = 'ak ah as ah', texture = 'atx') {
  return stack(atlasDrums(drums), atlasTexture(texture));
}
