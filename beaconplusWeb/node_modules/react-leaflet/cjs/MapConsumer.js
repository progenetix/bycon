"use strict";

exports.__esModule = true;
exports.MapConsumer = MapConsumer;

var _hooks = require("./hooks");

function MapConsumer(_ref) {
  let {
    children
  } = _ref;
  return children((0, _hooks.useMap)());
}