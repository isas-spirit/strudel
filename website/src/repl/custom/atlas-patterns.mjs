import { Pattern } from '@strudel/core';

Pattern.prototype.atlasSwing = function (subdivision = 4, amount = 1 / 3) {
  return this.swingBy(amount, subdivision);
};

Pattern.prototype.atlasGhosts = function (offset = 1 / 8, ghostGain = 0.35) {
  return this.off(offset, (x) => x.gain(ghostGain));
};

Pattern.prototype.atlasTight = function (release = 0.05, end = 0.9) {
  return this.release(release).end(end);
};

export const atlasPatternExtensionsLoaded = true;
