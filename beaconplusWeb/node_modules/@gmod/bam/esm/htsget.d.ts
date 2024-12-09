/// <reference types="node" />
import { Buffer } from 'buffer';
import { BaseOpts, BamOpts } from './util';
import BamFile from './bamFile';
import Chunk from './chunk';
export default class HtsgetFile extends BamFile {
    private baseUrl;
    private trackId;
    constructor(args: {
        trackId: string;
        baseUrl: string;
    });
    streamRecordsForRange(chr: string, min: number, max: number, opts?: BamOpts): AsyncGenerator<import("./record").default[], void, unknown>;
    _readChunk({ chunk }: {
        chunk: Chunk;
        opts: BaseOpts;
    }): Promise<{
        data: Buffer;
        cpositions: never[];
        dpositions: never[];
        chunk: Chunk;
    }>;
    getHeader(opts?: BaseOpts): Promise<{
        tag: string;
        data: {
            tag: string;
            value: string;
        }[];
    }[]>;
}
