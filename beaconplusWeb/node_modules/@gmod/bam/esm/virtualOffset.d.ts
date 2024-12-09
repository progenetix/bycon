/// <reference types="node" />
export default class VirtualOffset {
    blockPosition: number;
    dataPosition: number;
    constructor(blockPosition: number, dataPosition: number);
    toString(): string;
    compareTo(b: VirtualOffset): number;
    static min(...args: VirtualOffset[]): VirtualOffset;
}
export declare function fromBytes(bytes: Buffer, offset?: number, bigendian?: boolean): VirtualOffset;
