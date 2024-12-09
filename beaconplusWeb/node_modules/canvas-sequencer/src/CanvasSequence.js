/*
 * Author: Michael van der Kamp
 * Date: July/August, 2018
 *
 * This file provides the definition of the CanvasSequence class.
 */

'use strict';

const CanvasAtom = require('./CanvasAtom.js');

const locals = Object.freeze({
  METHODS: [
    'addHitRegion',
    'arc',
    'arcTo',
    'beginPath',
    'bezierCurveTo',
    'clearHitRegions',
    'clearRect',
    'clip',
    'closePath',
    'drawFocusIfNeeded',
    'drawImage',
    'ellipse',
    'fill',
    'fillRect',
    'fillText',
    'lineTo',
    'moveTo',
    'putImageData',
    'quadraticCurveTo',
    'rect',
    'removeHitRegion',
    'resetTransform',
    'restore',
    'rotate',
    'save',
    'scale',
    'scrollPathIntoView',
    'setLineDash',
    'setTransform',
    'stroke',
    'strokeRect',
    'strokeText',
    'transform',
    'translate',
  ],

  PROPERTIES: [
    'direction',
    'fillStyle',
    'filter',
    'font',
    'globalAlpha',
    'globalCompositeOperation',
    'imageSmoothingEnabled',
    'imageSmoothingQuality',
    'lineCap',
    'lineDashOffset',
    'lineJoin',
    'lineWidth',
    'miterLimit',
    'shadowBlur',
    'shadowColor',
    'shadowOffsetX',
    'shadowOffsetY',
    'strokeStyle',
    'textAlign',
    'textBaseline',
  ],
});

// Mark properties as intended for internal use.
const symbols = Object.freeze({
  sequence: Symbol.for('sequence'),
  push:     Symbol.for('push'),
  fromJSON: Symbol.for('fromJSON'),
});

/**
 * A CanvasSequence is a linear collection of CanvasAtoms, capable of being
 * executed on a CanvasRenderingContext2D.
 *
 * @param {CanvasSequence} [data=null] - An unrevived (i.e. freshly transmitted)
 * CanvasSequence. If present, the constructor revives the sequence. Note that
 * an already revived CanvasSequence cannot be used as the argument here.
 */
class CanvasSequence {
  constructor(data = null) {
    /**
     * The CanvasAtoms that form the sequence.
     *
     * @private
     * @type {CanvasAtom[]}
     */
    this[symbols.sequence] = [];

    // If data is present, assume it is a CanvasSequence that needs reviving.
    if (data) this[symbols.fromJSON](data);
  }

  /**
   * Revive the sequence from transmitted JSON data.
   *
   * @private
   * @param {CanvasSequence} [data={}]
   */
  [symbols.fromJSON](data = { sequence: [] }) {
    data.sequence.forEach(({ type, inst, args }) => {
      this[symbols.push](type, inst, args);
    });
  }

  /**
   * Push a new CanvasAtom onto the end of the sequence.
   *
   * @private
   * @param {string} type - The type of CanvasAtom to push.
   * @param {string} inst - The canvas context instruction.
   * @param {*[]} args - The arguments to the canvas context instruction.
   */
  [symbols.push](type, inst, args) {
    this[symbols.sequence].push(new CanvasAtom(type, inst, args));
  }

  /**
   * Execute the sequence on the given context.
   *
   * @param {CanvasRenderingContext2D} context
   */
  execute(context) {
    context.save();
    this[symbols.sequence].forEach(a => a.execute(context));
    context.restore();
  }

  /**
   * Export a JSON serialized version of the sequence, ready for transmission.
   *
   * @return {CanvasSequence} In JSON serialized form.
   */
  toJSON() {
    return { sequence: this[symbols.sequence] };
  }
}

locals.METHODS.forEach(m => {
  Object.defineProperty(CanvasSequence.prototype, m, {
    value: function pushMethodCall(...args) {
      this[symbols.push](CanvasAtom.METHOD, m, args);
    },
    writable:     false,
    enumerable:   true,
    configurable: false,
  });
});

locals.PROPERTIES.forEach(p => {
  Object.defineProperty(CanvasSequence.prototype, p, {
    get()  { throw `Invalid canvas sequencer interaction, cannot get ${p}.`; },
    set(v) { this[symbols.push](CanvasAtom.PROPERTY, p, [v]); },
    enumerable:   true,
    configurable: false,
  });
});

module.exports = CanvasSequence;

