import { createPathComponent } from '@react-leaflet/core';
import { FeatureGroup as LeafletFeatureGroup } from 'leaflet';
export const FeatureGroup = createPathComponent(function createFeatureGroup(_ref, ctx) {
  let {
    children: _c,
    ...options
  } = _ref;
  const instance = new LeafletFeatureGroup([], options);
  const context = { ...ctx,
    layerContainer: instance,
    overlayContainer: instance
  };
  return {
    instance,
    context
  };
});