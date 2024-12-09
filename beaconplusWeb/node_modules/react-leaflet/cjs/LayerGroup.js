"use strict";

exports.__esModule = true;
exports.LayerGroup = void 0;

var _core = require("@react-leaflet/core");

var _leaflet = require("leaflet");

const LayerGroup = (0, _core.createLayerComponent)(function createLayerGroup(_ref, ctx) {
  let {
    children: _c,
    ...options
  } = _ref;
  const instance = new _leaflet.LayerGroup([], options);
  return {
    instance,
    context: { ...ctx,
      layerContainer: instance
    }
  };
});
exports.LayerGroup = LayerGroup;