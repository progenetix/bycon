import { GenericFilehandle } from 'generic-filehandle';
import Chunk from './chunk';
import { BaseOpts } from './util';
export default abstract class IndexFile {
    filehandle: GenericFilehandle;
    renameRefSeq: (s: string) => string;
    /**
     * @param {filehandle} filehandle
     * @param {function} [renameRefSeqs]
     */
    constructor({ filehandle, renameRefSeq, }: {
        filehandle: GenericFilehandle;
        renameRefSeq?: (a: string) => string;
    });
    abstract lineCount(refId: number): Promise<number>;
    abstract indexCov(refId: number, start?: number, end?: number): Promise<{
        start: number;
        end: number;
        score: number;
    }[]>;
    abstract blocksForRange(chrId: number, start: number, end: number, opts?: BaseOpts): Promise<Chunk[]>;
}
