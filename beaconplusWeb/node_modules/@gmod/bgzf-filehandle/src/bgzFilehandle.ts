import { Buffer } from 'buffer'
import { LocalFile, GenericFilehandle } from 'generic-filehandle'

// locals
import { unzip } from './unzip'
import GziIndex from './gziIndex'

export default class BgzFilehandle {
  filehandle: GenericFilehandle
  gzi: GziIndex

  constructor({
    filehandle,
    path,
    gziFilehandle,
    gziPath,
  }: {
    filehandle?: GenericFilehandle
    path?: string
    gziFilehandle?: GenericFilehandle
    gziPath?: string
  }) {
    if (filehandle) {
      this.filehandle = filehandle
    } else if (path) {
      this.filehandle = new LocalFile(path)
    } else {
      throw new TypeError('either filehandle or path must be defined')
    }

    if (!gziFilehandle && !gziPath && !path) {
      throw new TypeError('either gziFilehandle or gziPath must be defined')
    }

    this.gzi = new GziIndex({
      filehandle: gziFilehandle,
      path: !gziFilehandle && !gziPath && path ? gziPath : `${path}.gzi`,
    })
  }

  async stat() {
    const compressedStat = await this.filehandle.stat()
    return Object.assign(compressedStat, {
      size: await this.getUncompressedFileSize(),
      blocks: undefined,
      blksize: undefined,
    })
  }

  async getUncompressedFileSize() {
    // read the last block's ISIZE (see gzip RFC),
    // and add it to its uncompressedPosition
    const [, uncompressedPosition] = await this.gzi.getLastBlock()

    const { size } = await this.filehandle.stat()

    const buf = Buffer.allocUnsafe(4)
    // note: there should be a 28-byte EOF marker (an empty block) at
    // the end of the file, so we skip backward past that
    const { bytesRead } = await this.filehandle.read(buf, 0, 4, size - 28 - 4)
    if (bytesRead !== 4) {
      throw new Error('read error')
    }
    const lastBlockUncompressedSize = buf.readUInt32LE(0)
    return uncompressedPosition + lastBlockUncompressedSize
  }

  async _readAndUncompressBlock(
    blockBuffer: Buffer,
    [compressedPosition]: [number],
    [nextCompressedPosition]: [number],
  ) {
    let next = nextCompressedPosition
    if (!next) {
      next = (await this.filehandle.stat()).size
    }

    // read the compressed data into the block buffer
    const blockCompressedLength = next - compressedPosition

    await this.filehandle.read(
      blockBuffer,
      0,
      blockCompressedLength,
      compressedPosition,
    )

    // uncompress it
    const unzippedBuffer = await unzip(
      blockBuffer.slice(0, blockCompressedLength),
    )

    return unzippedBuffer as Buffer
  }

  async read(buf: Buffer, offset: number, length: number, position: number) {
    // get the block positions for this read
    const blockPositions = await this.gzi.getRelevantBlocksForRead(
      length,
      position,
    )
    const blockBuffer = Buffer.allocUnsafe(32768 * 2)
    // uncompress the blocks and read from them one at a time to keep memory usage down
    let destinationOffset = offset
    let bytesRead = 0
    for (
      let blockNum = 0;
      blockNum < blockPositions.length - 1;
      blockNum += 1
    ) {
      // eslint-disable-next-line no-await-in-loop
      const uncompressedBuffer = await this._readAndUncompressBlock(
        blockBuffer,
        blockPositions[blockNum],
        blockPositions[blockNum + 1],
      )
      const [, uncompressedPosition] = blockPositions[blockNum]
      const sourceOffset =
        uncompressedPosition >= position ? 0 : position - uncompressedPosition
      const sourceEnd =
        Math.min(
          position + length,
          uncompressedPosition + uncompressedBuffer.length,
        ) - uncompressedPosition
      if (sourceOffset >= 0 && sourceOffset < uncompressedBuffer.length) {
        uncompressedBuffer.copy(buf, destinationOffset, sourceOffset, sourceEnd)
        destinationOffset += sourceEnd - sourceOffset
        bytesRead += sourceEnd - sourceOffset
      }
    }

    return { bytesRead, buffer: buf }
  }
}
