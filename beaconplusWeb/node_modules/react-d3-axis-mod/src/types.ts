export type Scaler<T> = (x: T) => number;

export type Orients = 'TOP' | 'RIGHT' | 'BOTTOM' | 'LEFT';
export type AxisStyle = {
  orient: Orients;
  tickSizeInner: number;
  tickSizeOuter: number;
  tickPadding: number;
  strokeWidth: number;
  tickFont: string;
  tickFontSize: number;
};
