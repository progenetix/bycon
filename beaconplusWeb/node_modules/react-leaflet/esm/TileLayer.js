import { createTileLayerComponent, updateGridLayer, withPane } from '@react-leaflet/core';
import { TileLayer as LeafletTileLayer } from 'leaflet';
export const TileLayer = createTileLayerComponent(function createTileLayer(_ref, context) {
  let {
    url,
    ...options
  } = _ref;
  return {
    instance: new LeafletTileLayer(url, withPane(options, context)),
    context
  };
}, updateGridLayer);