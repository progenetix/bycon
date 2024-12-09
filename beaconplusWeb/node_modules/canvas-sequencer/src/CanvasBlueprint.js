/*
 * Author: Michael van der Kamp
 * Date: July/August, 2018
 *
 * Thie file provides the definition of the CanvasBlueprint class.
 *
 * A CanvasBlueprint is similar to a plain CanvasSequence, except that it
 * accepts tag strings as arguments, and before it can be executed it  needs to
 * be 'built' with an object defining which values should replace the tags.
 */

'use strict';

const CanvasSequence = require('./CanvasSequence.js');

// Mark properties as intended for internal use.
const symbols = Object.freeze({
  sequence: Symbol.for('sequence'),
  push:     Symbol.for('push'),
});

/**
 * Replace tags in the given string with correlated value in values.
 *
 * Rules:
 * - Strings not surrounded by curly braces {} will be returned.
 * - Strings surrounded by curly braces but not corresponding to a property on
 *   'values' will result in a string without the curly braces being returned.
 * - Strings surrounded by curly braces, with the inner string corresponding to
 *   a property on 'values' will result in the corresponding value being
 *   returned.
 *
 * @inner
 * @private
 *
 * @param {string} str
 * @param {object} values
 *
 * @return {string|mixed} Either the original string if no replacement was
 * performed, or the appropriate value.
 */
function replaceTags(str, values) {
  const tag = str.replace(/^\{|\}$/gu, '');
  if (tag !== str) {
    return values.hasOwnProperty(tag) ? values[tag] : tag;
  }
  return str;
}

/**
 * A CanvasBlueprint is a rebuildable CanvasSequence. It accepts tagged
 * arguments. When built, tags will be replaced using properties from a provided
 * object.
 *
 * @extends CanvasSequence
 */
class CanvasBlueprint extends CanvasSequence {
  /**
   * Build the blueprint using the provided values.
   *
   * Rules:
   * - Strings not surrounded by curly braces {} will be returned.
   * - Strings surrounded by curly braces but not corresponding to a property on
   *   'values' will result in a string without the curly braces being returned.
   * - Strings surrounded by curly braces, with the inner string corresponding
   *   to a property on 'values' will result in the corresponding value being
   *   returned.
   *
   * @param {object} values - The values with which to construct the sequence.
   *
   * @return {CanvasSequence} The constructed sequence.
   */
  build(values = {}) {
    const seq = new CanvasSequence();
    this[symbols.sequence].forEach(({ type, inst, args }) => {
      const realArgs = args.map(v => {
        return (typeof v === 'string') ? replaceTags(v, values) : v;
      });
      seq[symbols.push](type, inst, realArgs);
    });
    return seq;
  }

  /**
   * CanvasBlueprints cannot be directly executed!
   *
   * @throws TypeError
   */
  execute() {
    throw new TypeError('Cannot execute a blueprint.');
  }
}

module.exports = CanvasBlueprint;

