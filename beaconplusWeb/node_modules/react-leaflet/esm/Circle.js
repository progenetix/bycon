import { createPathComponent, updateCircle } from '@react-leaflet/core';
import { Circle as LeafletCircle } from 'leaflet';
export const Circle = createPathComponent(function createCircle(_ref, ctx) {
  let {
    center,
    children: _c,
    ...options
  } = _ref;
  const instance = new LeafletCircle(center, options);
  return {
    instance,
    context: { ...ctx,
      overlayContainer: instance
    }
  };
}, updateCircle);