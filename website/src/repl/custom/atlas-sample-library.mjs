import { samples } from '@strudel/webaudio';

const { BASE_URL } = import.meta.env;
const baseNoTrailing = BASE_URL.endsWith('/') ? BASE_URL.slice(0, -1) : BASE_URL;

export const ATLAS_FOUNDATION_PACK = 'atlas-foundation';

export function atlasPackUrl(pack = ATLAS_FOUNDATION_PACK, version = '1') {
  return `${baseNoTrailing}/user-samples/${pack}/strudel.json?v=${version}`;
}

export function loadAtlasPack(pack = ATLAS_FOUNDATION_PACK, version = '1', options = {}) {
  return samples(atlasPackUrl(pack, version), '', options);
}

export function preloadAtlasFoundation(options = {}) {
  return loadAtlasPack(ATLAS_FOUNDATION_PACK, '1', { prebake: true, tag: 'user', ...options });
}

export const atlasSampleLibrary = {
  baseNoTrailing,
  atlasPackUrl,
  loadAtlasPack,
  preloadAtlasFoundation,
};
