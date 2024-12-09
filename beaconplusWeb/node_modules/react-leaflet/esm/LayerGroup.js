import { createLayerComponent } from '@react-leaflet/core';
import { LayerGroup as LeafletLayerGroup } from 'leaflet';
export const LayerGroup = createLayerComponent(function createLayerGroup(_ref, ctx) {
  let {
    children: _c,
    ...options
  } = _ref;
  const instance = new LeafletLayerGroup([], options);
  return {
    instance,
    context: { ...ctx,
      layerContainer: instance
    }
  };
});