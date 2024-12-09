import { Buffer } from 'buffer'
import { inflateRaw } from 'pako'

export function unzip(input: Buffer) {
  return inflateRaw(input.subarray(2))
}
