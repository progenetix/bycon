import { useMap } from './hooks';
export function MapConsumer(_ref) {
  let {
    children
  } = _ref;
  return children(useMap());
}