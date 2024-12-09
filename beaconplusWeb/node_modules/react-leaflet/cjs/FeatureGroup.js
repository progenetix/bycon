"use strict";

exports.__esModule = true;
exports.FeatureGroup = void 0;

var _core = require("@react-leaflet/core");

var _leaflet = require("leaflet");

const FeatureGroup = (0, _core.createPathComponent)(function createFeatureGroup(_ref, ctx) {
  let {
    children: _c,
    ...options
  } = _ref;
  const instance = new _leaflet.FeatureGroup([], options);
  const context = { ...ctx,
    layerContainer: instance,
    overlayContainer: instance
  };
  return {
    instance,
    context
  };
});
exports.FeatureGroup = FeatureGroup;