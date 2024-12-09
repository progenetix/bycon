import { createTileLayerComponent, updateGridLayer, withPane } from '@react-leaflet/core';
import { TileLayer } from 'leaflet';
export const WMSTileLayer = createTileLayerComponent(function createWMSTileLayer(_ref, context) {
  let {
    params = {},
    url,
    ...options
  } = _ref;
  return {
    instance: new TileLayer.WMS(url, { ...params,
      ...withPane(options, context)
    }),
    context
  };
}, function updateWMSTileLayer(layer, props, prevProps) {
  updateGridLayer(layer, props, prevProps);

  if (props.params != null && props.params !== prevProps.params) {
    layer.setParams(props.params);
  }
});