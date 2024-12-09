import { Buffer } from 'buffer'
import { Observer } from 'rxjs'
import { Parser } from 'binary-parser'
import AbortablePromiseCache from 'abortable-promise-cache'
import { GenericFilehandle } from 'generic-filehandle'
import QuickLRU from 'quick-lru'

// locals
import Range from './range'
import { unzip } from './unzip'
import { Feature } from './bbi'
import { groupBlocks, checkAbortSignal } from './util'

interface CoordRequest {
  chrId: number
  start: number
  end: number
}
interface DataBlock {
  blockOffset: bigint
  blockSize: bigint
  startChrom: number
  endChrom: number
  startBase: number
  endBase: number
  validCnt: number
  minVal: number
  maxVal: number
  sumData: number
  sumSqData: number
}

interface ReadData {
  offset: bigint | number
  length: bigint | number
}

interface Options {
  signal?: AbortSignal
  request?: CoordRequest
}

const BIG_WIG_TYPE_GRAPH = 1
const BIG_WIG_TYPE_VSTEP = 2
const BIG_WIG_TYPE_FSTEP = 3

function coordFilter(s1: number, e1: number, s2: number, e2: number): boolean {
  return s1 < e2 && e1 >= s2
}

function getParsers(isBigEndian: boolean) {
  const le = isBigEndian ? 'big' : 'little'
  const summaryParser = new Parser()
    .endianess(le)
    .uint32('chromId')
    .uint32('start')
    .uint32('end')
    .uint32('validCnt')
    .floatle('minScore')
    .floatle('maxScore')
    .floatle('sumData')
    .floatle('sumSqData')
    .saveOffset('offset')

  const leafParser = new Parser()
    .endianess(le)
    .uint8('isLeaf')
    .skip(1)
    .uint16('cnt')
    .choice({
      tag: 'isLeaf',
      choices: {
        1: new Parser().endianess(le).array('blocksToFetch', {
          length: 'cnt',
          type: new Parser()
            .endianess(le)
            .uint32('startChrom')
            .uint32('startBase')
            .uint32('endChrom')
            .uint32('endBase')
            .uint64('blockOffset')
            .uint64('blockSize')
            .saveOffset('offset'),
        }),
        0: new Parser().array('recurOffsets', {
          length: 'cnt',
          type: new Parser()
            .endianess(le)
            .uint32('startChrom')
            .uint32('startBase')
            .uint32('endChrom')
            .uint32('endBase')
            .uint64('blockOffset')
            .saveOffset('offset'),
        }),
      },
    })
  const bigBedParser = new Parser()
    .endianess(le)
    .uint32('chromId')
    .int32('start')
    .int32('end')
    .string('rest', {
      zeroTerminated: true,
    })
    .saveOffset('offset')

  const bigWigParser = new Parser()
    .endianess(le)
    .skip(4)
    .int32('blockStart')
    .skip(4)
    .uint32('itemStep')
    .uint32('itemSpan')
    .uint8('blockType')
    .skip(1)
    .uint16('itemCount')
    .choice({
      tag: 'blockType',
      choices: {
        [BIG_WIG_TYPE_FSTEP]: new Parser().array('items', {
          length: 'itemCount',
          type: new Parser().floatle('score'),
        }),
        [BIG_WIG_TYPE_VSTEP]: new Parser().array('items', {
          length: 'itemCount',
          type: new Parser().endianess(le).int32('start').floatle('score'),
        }),
        [BIG_WIG_TYPE_GRAPH]: new Parser().array('items', {
          length: 'itemCount',
          type: new Parser()
            .endianess(le)
            .int32('start')
            .int32('end')
            .floatle('score'),
        }),
      },
    })
  return {
    bigWigParser,
    bigBedParser,
    summaryParser,
    leafParser,
  }
}

/**
 * View into a subset of the data in a BigWig file.
 *
 * Adapted by Robert Buels and Colin Diesh from bigwig.js in the Dalliance Genome
 * Explorer by Thomas Down.
 * @constructs
 */

export class BlockView {
  private cirTreePromise?: Promise<{ bytesRead: number; buffer: Buffer }>

  private featureCache = new AbortablePromiseCache<ReadData, Buffer>({
    cache: new QuickLRU({ maxSize: 1000 }),

    fill: async (requestData, signal) => {
      const len = Number(requestData.length)
      const off = Number(requestData.offset)
      const { buffer } = await this.bbi.read(Buffer.alloc(len), 0, len, off, {
        signal,
      })
      return buffer
    },
  })

  private leafParser: ReturnType<typeof getParsers>['leafParser']

  private bigBedParser: ReturnType<typeof getParsers>['bigBedParser']

  public constructor(
    private bbi: GenericFilehandle,
    private refsByName: any,
    private cirTreeOffset: number,
    private isBigEndian: boolean,
    private isCompressed: boolean,
    private blockType: string,
  ) {
    if (!(cirTreeOffset >= 0)) {
      throw new Error('invalid cirTreeOffset!')
    }

    const parsers = getParsers(isBigEndian)
    this.leafParser = parsers.leafParser
    this.bigBedParser = parsers.bigBedParser
  }

  public async readWigData(
    chrName: string,
    start: number,
    end: number,
    observer: Observer<Feature[]>,
    opts?: Options,
  ) {
    try {
      const { refsByName, bbi, cirTreeOffset, isBigEndian } = this
      const chrId = refsByName[chrName]
      if (chrId === undefined) {
        observer.complete()
      }
      const request = { chrId, start, end }
      if (!this.cirTreePromise) {
        this.cirTreePromise = bbi.read(
          Buffer.alloc(48),
          0,
          48,
          Number(cirTreeOffset),
          opts,
        )
      }
      const { buffer } = await this.cirTreePromise
      const cirBlockSize = isBigEndian
        ? buffer.readUInt32BE(4)
        : buffer.readUInt32LE(4)
      let blocksToFetch: any[] = []
      let outstanding = 0

      const cirFobRecur2 = (
        cirBlockData: Buffer,
        offset: number,
        level: number,
      ) => {
        try {
          const data = cirBlockData.subarray(offset)

          const p = this.leafParser.parse(data) as {
            blocksToFetch: DataBlock[]
            recurOffsets: DataBlock[]
          }
          if (p.blocksToFetch) {
            blocksToFetch = blocksToFetch.concat(
              p.blocksToFetch
                .filter(f => filterFeats(f))
                .map((l: { blockOffset: bigint; blockSize: bigint }) => ({
                  offset: l.blockOffset,
                  length: l.blockSize,
                })),
            )
          }
          if (p.recurOffsets) {
            const recurOffsets = p.recurOffsets
              .filter(f => filterFeats(f))
              .map(l => Number(l.blockOffset))
            if (recurOffsets.length > 0) {
              cirFobRecur(recurOffsets, level + 1)
            }
          }
        } catch (e) {
          observer.error(e)
        }
      }

      const filterFeats = (b: DataBlock) => {
        const { startChrom, startBase, endChrom, endBase } = b
        return (
          (startChrom < chrId || (startChrom === chrId && startBase <= end)) &&
          (endChrom > chrId || (endChrom === chrId && endBase >= start))
        )
      }

      const cirFobStartFetch = async (
        off: number[],
        fr: Range,
        level: number,
      ) => {
        try {
          const length = fr.max - fr.min
          const offset = fr.min
          const resultBuffer: Buffer = await this.featureCache.get(
            `${length}_${offset}`,
            { length, offset },
            opts?.signal,
          )
          for (const element of off) {
            if (fr.contains(element)) {
              cirFobRecur2(resultBuffer, element - offset, level)
              outstanding -= 1
              if (outstanding === 0) {
                this.readFeatures(observer, blocksToFetch, {
                  ...opts,
                  request,
                }).catch(e => observer.error(e))
              }
            }
          }
        } catch (e) {
          observer.error(e)
        }
      }
      const cirFobRecur = (offset: number[], level: number) => {
        try {
          outstanding += offset.length

          // Upper bound on size, based on a completely full leaf node.
          const maxCirBlockSpan = 4 + Number(cirBlockSize) * 32
          let spans = new Range([
            { min: offset[0], max: offset[0] + maxCirBlockSpan },
          ])
          for (let i = 1; i < offset.length; i += 1) {
            const blockSpan = new Range([
              { min: offset[i], max: offset[i] + maxCirBlockSpan },
            ])
            spans = spans.union(blockSpan)
          }
          spans.getRanges().map(fr => cirFobStartFetch(offset, fr, level))
        } catch (e) {
          observer.error(e)
        }
      }

      return cirFobRecur([Number(cirTreeOffset) + 48], 1)
    } catch (e) {
      observer.error(e)
    }
  }

  private parseSummaryBlock(
    buffer: Buffer,
    startOffset: number,
    request?: CoordRequest,
  ) {
    const features = [] as any[]
    let offset = startOffset

    const dataView = new DataView(
      buffer.buffer,
      buffer.byteOffset,
      buffer.length,
    )
    while (offset < buffer.byteLength) {
      // this was extracted from looking at the runtime code generated by
      // binary-parser
      const chromId = dataView.getUint32(offset, true)
      offset += 4
      const start = dataView.getUint32(offset, true)
      offset += 4
      const end = dataView.getUint32(offset, true)
      offset += 4
      const validCnt = dataView.getUint32(offset, true)
      offset += 4
      const minScore = dataView.getFloat32(offset, true)
      offset += 4
      const maxScore = dataView.getFloat32(offset, true)
      offset += 4
      const sumData = dataView.getFloat32(offset, true)
      offset += 4
      // unused
      // const sumSqData = dataView.getFloat32(offset, true)
      offset += 4

      if (
        request
          ? chromId === request.chrId &&
            coordFilter(start, end, request.start, request.end)
          : true
      ) {
        features.push({
          start,
          end,
          maxScore,
          minScore,
          summary: true,
          score: sumData / (validCnt || 1),
        })
      }
    }

    return features
  }

  private parseBigBedBlock(
    data: Buffer,
    startOffset: number,
    offset: number,
    request?: CoordRequest,
  ) {
    const items = [] as Feature[]
    let currOffset = startOffset
    while (currOffset < data.byteLength) {
      const res = this.bigBedParser.parse(data.subarray(currOffset))
      res.uniqueId = `bb-${offset + currOffset}`
      items.push(res)
      currOffset += res.offset
    }

    return request
      ? items.filter((f: any) =>
          coordFilter(f.start, f.end, request.start, request.end),
        )
      : items
  }

  private parseBigWigBlock(
    buffer: Buffer,
    startOffset: number,
    request?: CoordRequest,
  ) {
    const b = buffer.subarray(startOffset)

    const dataView = new DataView(b.buffer, b.byteOffset, b.length)
    let offset = 0
    offset += 4
    const blockStart = dataView.getInt32(offset, true)
    offset += 8
    const itemStep = dataView.getUint32(offset, true)
    offset += 4
    const itemSpan = dataView.getUint32(offset, true)
    offset += 4
    const blockType = dataView.getUint8(offset)
    offset += 2
    const itemCount = dataView.getUint16(offset, true)
    offset += 2
    const items = new Array(itemCount)
    switch (blockType) {
      case 1: {
        for (let i = 0; i < itemCount; i++) {
          const start = dataView.getInt32(offset, true)
          offset += 4
          const end = dataView.getInt32(offset, true)
          offset += 4
          const score = dataView.getFloat32(offset, true)
          offset += 4
          items[i] = { start, end, score }
        }
        break
      }
      case 2: {
        for (let i = 0; i < itemCount; i++) {
          const start = dataView.getInt32(offset, true)
          offset += 4
          const score = dataView.getFloat32(offset, true)
          offset += 4
          items[i] = { score, start, end: start + itemSpan }
        }
        break
      }
      case 3: {
        for (let i = 0; i < itemCount; i++) {
          const score = dataView.getFloat32(offset, true)
          offset += 4
          const start = blockStart + i * itemStep
          items[i] = { score, start, end: start + itemSpan }
        }
        break
      }
    }

    return request
      ? items.filter((f: any) =>
          coordFilter(f.start, f.end, request.start, request.end),
        )
      : items
  }

  public async readFeatures(
    observer: Observer<Feature[]>,
    blocks: { offset: bigint; length: bigint }[],
    opts: Options = {},
  ) {
    try {
      const { blockType, isCompressed } = this
      const { signal, request } = opts
      const blockGroupsToFetch = groupBlocks(blocks)
      checkAbortSignal(signal)
      await Promise.all(
        blockGroupsToFetch.map(async blockGroup => {
          checkAbortSignal(signal)
          const { length, offset } = blockGroup
          const data = await this.featureCache.get(
            `${length}_${offset}`,
            blockGroup,
            signal,
          )
          for (const block of blockGroup.blocks) {
            checkAbortSignal(signal)
            let blockOffset = Number(block.offset) - Number(blockGroup.offset)
            let resultData = data
            if (isCompressed) {
              resultData = unzip(data.subarray(blockOffset))
              blockOffset = 0
            }
            checkAbortSignal(signal)

            switch (blockType) {
              case 'summary': {
                observer.next(
                  this.parseSummaryBlock(resultData, blockOffset, request),
                )
                break
              }
              case 'bigwig': {
                observer.next(
                  this.parseBigWigBlock(resultData, blockOffset, request),
                )
                break
              }
              case 'bigbed': {
                observer.next(
                  this.parseBigBedBlock(
                    resultData,
                    blockOffset,
                    Number(block.offset) * (1 << 8),
                    request,
                  ),
                )
                break
              }
              default: {
                console.warn(`Don't know what to do with ${blockType}`)
              }
            }
          }
        }),
      )
      observer.complete()
    } catch (e) {
      observer.error(e)
    }
  }
}
