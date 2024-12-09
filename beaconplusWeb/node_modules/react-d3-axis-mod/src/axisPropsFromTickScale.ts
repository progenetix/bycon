import { ScaleLinear, ScaleQuantize } from 'd3-scale';

export default function axisPropsFromTickScale(
  scale: ScaleLinear<number, number, never> | ScaleQuantize<number, never>,
  tickCount: number,
) {
  const range = scale.range();
  const values = scale.ticks(tickCount);
  const format = scale.tickFormat(tickCount);
  const position = scale.copy();

  return {
    range,
    values,
    format,
    position,
  };
}
