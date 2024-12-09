/// <reference types="node" />
import VirtualOffset from './virtualOffset';
export default class Chunk {
    minv: VirtualOffset;
    maxv: VirtualOffset;
    bin: number;
    _fetchedSize?: number | undefined;
    buffer?: Buffer;
    constructor(minv: VirtualOffset, maxv: VirtualOffset, bin: number, _fetchedSize?: number | undefined);
    toUniqueString(): string;
    toString(): string;
    compareTo(b: Chunk): number;
    fetchedSize(): number;
}
