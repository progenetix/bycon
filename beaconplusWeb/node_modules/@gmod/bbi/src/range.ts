/* eslint prefer-rest-params:0, no-nested-ternary:0 */

/**
 * Adapted from a combination of Range and _Compound in the
 * Dalliance Genome Explorer, (c) Thomas Down 2006-2010.
 */

export interface IRange {
  min: number
  max: number
}
export default class Range {
  public ranges: IRange[]

  public constructor(arg1: IRange[]) {
    this.ranges = arg1
  }

  get min() {
    return this.ranges[0].min
  }

  get max() {
    return this.ranges[this.ranges.length - 1].max
  }

  public contains(pos: number) {
    for (const r of this.ranges) {
      if (r.min <= pos && r.max >= pos) {
        return true
      }
    }
    return false
  }

  public isContiguous(): boolean {
    return this.ranges.length > 1
  }

  public getRanges() {
    return this.ranges.map(r => new Range([{ min: r.min, max: r.max }]))
  }

  public toString(): string {
    return this.ranges.map(r => `[${r.min}-${r.max}]`).join(',')
  }

  public union(s1: Range): Range {
    const ranges = [...this.getRanges(), ...s1.getRanges()].sort((a, b) => {
      if (a.min < b.min) {
        return -1
      } else if (a.min > b.min) {
        return 1
      } else if (a.max < b.max) {
        return -1
      } else if (b.max > a.max) {
        return 1
      } else {
        return 0
      }
    })
    const oranges = []
    let current = ranges[0]

    for (let i = 1; i < ranges.length; i += 1) {
      const nxt = ranges[i]
      if (nxt.min > current.max + 1) {
        oranges.push(current)
        current = nxt
      } else if (nxt.max > current.max) {
        current = new Range([{ min: current.min, max: nxt.max }])
      }
    }
    oranges.push(current)

    return oranges.length === 1 ? oranges[0] : new Range(oranges)
  }
}
