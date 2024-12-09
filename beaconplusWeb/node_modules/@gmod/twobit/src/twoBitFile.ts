import Long from 'long'
import { LocalFile, GenericFilehandle } from 'generic-filehandle'
import { Parser } from '@gmod/binary-parser'

const TWOBIT_MAGIC = 0x1a412743

function tinyMemoize(_class: any, methodName: string) {
  const method = _class.prototype[methodName]
  const memoAttrName = `_memo_${methodName}`
  _class.prototype[methodName] = function _tinyMemoized() {
    if (!(memoAttrName in this)) {
      this[memoAttrName] = method.call(this)
    }
    return this[memoAttrName]
  }
}

const twoBit = ['T', 'C', 'A', 'G']
// byteTo4Bases is an array of byteValue -> 'ACTG'
// the weird `...keys()` incantation generates an array of numbers 0 to 255
const byteTo4Bases = [] as string[]
for (let i = 0; i < 256; i++) {
  byteTo4Bases.push(
    twoBit[(i >> 6) & 3] +
      twoBit[(i >> 4) & 3] +
      twoBit[(i >> 2) & 3] +
      twoBit[i & 3],
  )
}

type ParserName = 'header' | 'index' | 'record1' | 'record2' | 'record3'
const maskedByteTo4Bases = byteTo4Bases.map(bases => bases.toLowerCase())

export default class TwoBitFile {
  private filehandle: GenericFilehandle
  private isBigEndian?: boolean
  private version?: number

  /**
   * @param {object} args
   * @param {string} [args.path] filesystem path for the .2bit file to open
   * @param {Filehandle} [args.filehandle] node fs.promises-like filehandle for the .2bit file.
   *  Only needs to support `filehandle.read(buffer, offset, length, position)`
   */
  constructor({
    filehandle,
    path,
  }: {
    filehandle?: GenericFilehandle
    path?: string
  }) {
    if (filehandle) {
      this.filehandle = filehandle
    } else if (path) {
      this.filehandle = new LocalFile(path)
    } else {
      throw new Error('must supply path or filehandle')
    }
    this.isBigEndian = undefined
  }

  async _getParser(name: ParserName) {
    const parser = (await this._getParsers())[name]
    if (!parser) {
      throw new Error(`parser ${name} not found`)
    }
    return parser
  }

  async _detectEndianness() {
    const ret = await this.filehandle.read(Buffer.allocUnsafe(8), 0, 8, 0)
    const { buffer } = ret
    if (buffer.readInt32LE(0) === TWOBIT_MAGIC) {
      this.isBigEndian = false
      this.version = buffer.readInt32LE(4)
    } else if (buffer.readInt32BE(0) === TWOBIT_MAGIC) {
      this.isBigEndian = true
      this.version = buffer.readInt32BE(4)
    } else {
      throw new Error('not a 2bit file')
    }
  }

  // memoize
  /**
   * @private
   * detects the file's endianness and instantiates our binary parsers accordingly
   */
  async _getParsers() {
    await this._detectEndianness()

    const endianess = this.isBigEndian ? 'big' : 'little'
    const lebe = this.isBigEndian ? 'be' : 'le'

    let indexEntryParser = new Parser()
      .endianess(endianess)
      .uint8('nameLength')
      .string('name', { length: 'nameLength' })
    if (this.version === 1) {
      indexEntryParser = indexEntryParser.buffer('offsetBytes', {
        length: 8,
      })
    } else {
      indexEntryParser = indexEntryParser.uint32('offset')
    }
    /* istanbul ignore next */
    const header = new Parser()
      .endianess(endianess)
      .int32('magic', {
        assert: (m: number) => m === 0x1a412743,
      })
      .int32('version', {
        /* istanbul ignore next */
        assert: (v: number) => v === 0 || v === 1,
      })
      .uint32('sequenceCount', {
        /* istanbul ignore next */
        assert: (v: number) => v >= 0,
      })
      .uint32('reserved')

    return {
      header,
      index: new Parser()
        .endianess(endianess)
        .uint32('sequenceCount')
        .uint32('reserved')
        .array('index', {
          length: 'sequenceCount',
          type: indexEntryParser,
        }),
      record1: new Parser()
        .endianess(endianess)
        .uint32('dnaSize')
        .uint32('nBlockCount'),
      record2: new Parser()
        .endianess(endianess)
        .uint32('nBlockCount')
        .array('nBlockStarts', {
          length: 'nBlockCount',
          type: `uint32${lebe}`,
        })
        .array('nBlockSizes', {
          length: 'nBlockCount',
          type: `uint32${lebe}`,
        })
        .uint32('maskBlockCount'),
      record3: new Parser()
        .endianess(endianess)
        .uint32('maskBlockCount')
        .array('maskBlockStarts', {
          length: 'maskBlockCount',
          type: `uint32${lebe}`,
        })
        .array('maskBlockSizes', {
          length: 'maskBlockCount',
          type: `uint32${lebe}`,
        })
        .int32('reserved'),
      // .buffer('packedDna', { length: 'dnaSize' }),
    }
  }

  // memoize
  /**
   * @returns {Promise} for object with the file's header information, like
   *  `{ magic: 0x1a412743, version: 0, sequenceCount: 42, reserved: 0 }`
   */
  async getHeader() {
    await this._detectEndianness()

    const { buffer } = await this.filehandle.read(
      Buffer.allocUnsafe(16),
      0,
      16,
      0,
    )
    const headerParser = await this._getParser('header')
    return headerParser.parse(buffer).result
  }

  // memoize
  /**
   * @returns {Promise} for object with the file's index of offsets, like `{ seqName: fileOffset, ...}`
   */
  async getIndex() {
    const header = await this.getHeader()
    const maxIndexLength =
      8 + header.sequenceCount * (1 + 256 + (this.version === 1 ? 8 : 4))
    const { buffer } = await this.filehandle.read(
      Buffer.allocUnsafe(maxIndexLength),
      0,
      maxIndexLength,
      8,
    )
    const indexParser = await this._getParser('index')
    const indexData = indexParser.parse(buffer).result.index
    const index = {} as { [key: string]: number }
    if (this.version === 1) {
      indexData.forEach(
        ({ name, offsetBytes }: { name: string; offsetBytes: number }) => {
          const long = Long.fromBytes(offsetBytes, true, !this.isBigEndian)
          if (long.greaterThan(Number.MAX_SAFE_INTEGER)) {
            throw new Error(
              'integer overflow. File offset greater than 2^53-1 encountered. This library can only handle offsets up to 2^53-1.',
            )
          }
          index[name] = long.toNumber()
        },
      )
    } else {
      indexData.forEach(
        ({ name, offset }: { name: string; offset: number }) => {
          index[name] = offset
        },
      )
    }
    return index
  }

  /**
   * @returns {Promise} for an array of string sequence names that are found in the file
   */
  async getSequenceNames() {
    const index = await this.getIndex()
    return Object.keys(index)
  }

  /**
   * @returns {Promise} for an object listing the lengths of all sequences like `{seqName: length, ...}`
   */
  async getSequenceSizes() {
    const index = await this.getIndex()
    const seqNames = Object.keys(index)
    const sizePromises = Object.values(index).map(offset =>
      this._getSequenceSize(offset as number),
    )
    const sizes = await Promise.all(sizePromises)
    const returnObject = {} as { [key: string]: number }
    for (let i = 0; i < seqNames.length; i += 1) {
      returnObject[seqNames[i]] = sizes[i]
    }
    return returnObject
  }

  /**
   * @param {string} seqName name of the sequence
   * @returns {Promise} for the sequence's length, or undefined if it is not in the file
   */
  async getSequenceSize(seqName: string) {
    const index = await this.getIndex()
    const offset = index[seqName]
    if (!offset) {
      return undefined
    }
    return this._getSequenceSize(offset)
  }

  async _getSequenceSize(offset: number) {
    // we have to parse the sequence record in 3 parts, because we have to buffer 3 fixed-length file reads
    if (offset === undefined || offset < 0) {
      throw new Error('invalid offset')
    }
    const rec1 = await this._parseItem(offset, 8, 'record1')
    return rec1.dnaSize
  }

  async _getSequenceRecord(offset: number) {
    // we have to parse the sequence record in 3 parts, because we have to buffer 3 fixed-length file reads
    if (offset === undefined || offset < 0) {
      throw new Error('invalid offset')
    }
    const rec1 = await this._parseItem(offset, 8, 'record1')
    const rec2DataLength = rec1.nBlockCount * 8 + 8
    const rec2 = await this._parseItem(offset + 4, rec2DataLength, 'record2')
    const rec3DataLength = rec2.maskBlockCount * 8 + 8
    const rec3 = await this._parseItem(
      offset + 4 + rec2DataLength - 4,
      rec3DataLength,
      'record3',
    )

    const rec = {
      dnaSize: rec1.dnaSize,
      nBlocks: { starts: rec2.nBlockStarts, sizes: rec2.nBlockSizes },
      maskBlocks: { starts: rec3.maskBlockStarts, sizes: rec3.maskBlockSizes },
      dnaPosition: offset + 4 + rec2DataLength - 4 + rec3DataLength,
    }
    return rec
  }

  async _parseItem(offset: number, length: number, parserName: ParserName) {
    const { buffer } = await this.filehandle.read(
      Buffer.allocUnsafe(length),
      0,
      length,
      offset,
    )
    const parser = await this._getParser(parserName)
    return parser.parse(buffer).result
  }

  /**
   * @param {string} seqName name of the sequence you want
   * @param {number} [regionStart] optional 0-based half-open start of the sequence region to fetch.
   * @param {number} [regionEnd] optional 0-based half-open end of the sequence region to fetch. defaults to end of the sequence
   * @returns {Promise} for a string of sequence bases
   */
  async getSequence(seqName: string, regionStart = 0, regionEnd: number) {
    const index = await this.getIndex()
    const offset = index[seqName]
    if (!offset) {
      return undefined
    }
    // fetch the record for the seq
    const record = await this._getSequenceRecord(offset)

    if (regionStart < 0) {
      throw new TypeError('regionStart cannot be less than 0')
    }
    // end defaults to the end of the sequence
    if (regionEnd === undefined || regionEnd > record.dnaSize) {
      regionEnd = record.dnaSize
    }

    const nBlocks = this._getOverlappingBlocks(
      regionStart,
      regionEnd,
      record.nBlocks.starts,
      record.nBlocks.sizes,
    )
    const maskBlocks = this._getOverlappingBlocks(
      regionStart,
      regionEnd,
      record.maskBlocks.starts,
      record.maskBlocks.sizes,
    )

    const baseBytes = Buffer.allocUnsafe(
      Math.ceil((regionEnd - regionStart) / 4) + 1,
    )
    const baseBytesOffset = Math.floor(regionStart / 4)
    const { buffer } = await this.filehandle.read(
      baseBytes,
      0,
      baseBytes.length,
      record.dnaPosition + baseBytesOffset,
    )

    let sequenceBases = ''
    for (
      let genomicPosition = regionStart;
      genomicPosition < regionEnd;
      genomicPosition += 1
    ) {
      // check whether we are currently masked
      while (maskBlocks.length && maskBlocks[0].end <= genomicPosition) {
        maskBlocks.shift()
      }
      const baseIsMasked =
        maskBlocks[0] &&
        maskBlocks[0].start <= genomicPosition &&
        maskBlocks[0].end > genomicPosition

      // process the N block if we have one
      if (
        nBlocks[0] &&
        genomicPosition >= nBlocks[0].start &&
        genomicPosition < nBlocks[0].end
      ) {
        const currentNBlock = nBlocks.shift()
        for (
          ;
          genomicPosition < currentNBlock.end && genomicPosition < regionEnd;
          genomicPosition += 1
        ) {
          sequenceBases += baseIsMasked ? 'n' : 'N'
        }
        genomicPosition -= 1
      } else {
        const bytePosition = Math.floor(genomicPosition / 4) - baseBytesOffset
        const subPosition = genomicPosition % 4
        const byte = buffer[bytePosition]
        sequenceBases += baseIsMasked
          ? maskedByteTo4Bases[byte][subPosition]
          : byteTo4Bases[byte][subPosition]
      }
    }

    return sequenceBases
  }

  _getOverlappingBlocks(
    regionStart: number,
    regionEnd: number,
    blockStarts: number[],
    blockSizes: number[],
  ) {
    // find the start and end indexes of the blocks that match
    let startIndex
    let endIndex
    for (let i = 0; i < blockStarts.length; i += 1) {
      const blockStart = blockStarts[i]
      const blockSize = blockSizes[i]
      if (regionStart >= blockStart + blockSize || regionEnd <= blockStart) {
        // block does not overlap the region
        if (startIndex !== undefined) {
          endIndex = i
          break
        }
      } else if (startIndex === undefined) {
        startIndex = i
      } // block does overlap the region, record this if it is the first
    }

    if (startIndex === undefined) {
      return []
    }

    // now format some block objects to return
    if (endIndex === undefined) {
      endIndex = blockStarts.length
    }

    const blocks = new Array(endIndex - startIndex)
    for (let blockNum = startIndex; blockNum < endIndex; blockNum += 1) {
      blocks[blockNum - startIndex] = {
        start: blockStarts[blockNum],
        end: blockStarts[blockNum] + blockSizes[blockNum],
        size: blockSizes[blockNum],
      }
    }
    return blocks
  }
}

tinyMemoize(TwoBitFile, '_getParsers')
tinyMemoize(TwoBitFile, 'getIndex')
tinyMemoize(TwoBitFile, 'getHeader')
