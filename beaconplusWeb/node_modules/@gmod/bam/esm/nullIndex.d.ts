import IndexFile from './indexFile';
export default class NullIndex extends IndexFile {
    lineCount(): Promise<any>;
    protected _parse(): Promise<any>;
    indexCov(): Promise<any>;
    blocksForRange(): Promise<any>;
}
