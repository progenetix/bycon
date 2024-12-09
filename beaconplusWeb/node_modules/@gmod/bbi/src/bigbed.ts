import { Buffer } from 'buffer'
import { Parser } from 'binary-parser'
import { Observable, merge, firstValueFrom } from 'rxjs'
import { map, reduce } from 'rxjs/operators'
import AbortablePromiseCache from 'abortable-promise-cache'
import QuickLRU from 'quick-lru'

import { BBI, Feature, RequestOptions } from './bbi'

interface Loc {
  key: string
  offset: bigint
  length: bigint
  field?: number
}

interface Index {
  type: number
  fieldcount: number
  offset: number
  field: number
}

export function filterUndef<T>(ts: (T | undefined)[]): T[] {
  return ts.filter((t: T | undefined): t is T => !!t)
}

export class BigBed extends BBI {
  public readIndicesCache = new AbortablePromiseCache<RequestOptions, Index[]>({
    cache: new QuickLRU({ maxSize: 1 }),
    fill: (args: RequestOptions, signal?: AbortSignal) =>
      this._readIndices({ ...args, signal }),
  })

  public readIndices(opts: RequestOptions = {}) {
    const { signal, ...rest } = opts
    return this.readIndicesCache.get(JSON.stringify(rest), opts, signal)
  }

  /*
   * retrieve unzoomed view for any scale
   */
  protected async getView(_scale: number, opts?: RequestOptions) {
    return this.getUnzoomedView(opts)
  }

  /*
   * parse the bigbed extraIndex fields
   * @param abortSignal to abort operation
   * @return a Promise for an array of Index data structure since there can be multiple extraIndexes in a bigbed, see bedToBigBed documentation
   */
  private async _readIndices(opts: RequestOptions) {
    const { extHeaderOffset, isBigEndian } = await this.getHeader(opts)
    const { buffer: data } = await this.bbi.read(
      Buffer.alloc(64),
      0,
      64,
      Number(extHeaderOffset),
    )
    const le = isBigEndian ? 'big' : 'little'
    const ret = new Parser()
      .endianess(le)
      .uint16('size')
      .uint16('count')
      .uint64('offset')
      .parse(data)

    const { count, offset } = ret

    // no extra index is defined if count==0
    if (count === 0) {
      return []
    }

    const blocklen = 20
    const len = blocklen * count
    const { buffer } = await this.bbi.read(
      Buffer.alloc(len),
      0,
      len,
      Number(offset),
    )
    const extParser = new Parser()
      .endianess(le)
      .int16('type')
      .int16('fieldcount')
      .uint64('offset')
      .skip(4)
      .int16('field')
    const indices = [] as Index[]

    for (let i = 0; i < count; i += 1) {
      indices.push(extParser.parse(buffer.subarray(i * blocklen)))
    }
    return indices
  }

  /*
   * perform a search in the bigbed extraIndex to find which blocks in the bigbed data to look for the
   * actual feature data
   *
   * @param name - the name to search for
   * @param opts - a SearchOptions argument with optional signal
   * @return a Promise for an array of bigbed block Loc entries
   */
  private async searchExtraIndexBlocks(
    name: string,
    opts: RequestOptions = {},
  ): Promise<Loc[]> {
    const { isBigEndian } = await this.getHeader(opts)
    const indices = await this.readIndices(opts)
    if (indices.length === 0) {
      return []
    }
    const locs = indices.map(async (index: any): Promise<Loc | undefined> => {
      const { offset, field } = index
      const { buffer: data } = await this.bbi.read(
        Buffer.alloc(32),
        0,
        32,
        Number(offset),
        opts,
      )
      const le = isBigEndian ? 'big' : 'little'
      const p = new Parser()
        .endianess(le)
        .int32('magic')
        .int32('blockSize')
        .int32('keySize')
        .int32('valSize')
        .uint64('itemCount')

      const { blockSize, keySize, valSize } = p.parse(data)
      // console.log({blockSize,keySize,valSize})
      const bpt = new Parser()
        .endianess(le)
        .int8('nodeType')
        .skip(1)
        .int16('cnt')
        .choice({
          tag: 'nodeType',
          choices: {
            0: new Parser().array('leafkeys', {
              length: 'cnt',
              type: new Parser()
                .endianess(le)
                .string('key', { length: keySize, stripNull: true })
                .uint64('offset'),
            }),
            1: new Parser().array('keys', {
              length: 'cnt',
              type: new Parser()
                .endianess(le)
                .string('key', { length: keySize, stripNull: true })
                .uint64('offset')
                .uint32('length')
                .uint32('reserved'),
            }),
          },
        })

      const bptReadNode = async (
        nodeOffset: number,
      ): Promise<Loc | undefined> => {
        const val = Number(nodeOffset)
        const len = 4 + blockSize * (keySize + valSize)
        const { buffer } = await this.bbi.read(
          Buffer.alloc(len),
          0,
          len,
          val,
          opts,
        )
        const node = bpt.parse(buffer)
        if (node.leafkeys) {
          let lastOffset
          for (let i = 0; i < node.leafkeys.length; i += 1) {
            const { key } = node.leafkeys[i]
            if (name.localeCompare(key) < 0 && lastOffset) {
              return bptReadNode(lastOffset)
            }
            lastOffset = node.leafkeys[i].offset
          }
          return bptReadNode(lastOffset)
        }
        for (let i = 0; i < node.keys.length; i += 1) {
          if (node.keys[i].key === name) {
            return { ...node.keys[i], field }
          }
        }

        return undefined
      }
      const rootNodeOffset = 32
      return bptReadNode(Number(offset) + rootNodeOffset)
    })
    return filterUndef(await Promise.all(locs))
  }

  /*
   * retrieve the features from the bigbed data that were found through the lookup of the extraIndex
   * note that there can be multiple extraIndex, see the BigBed specification and the -extraIndex argument to bedToBigBed
   *
   * @param name - the name to search for
   * @param opts - a SearchOptions argument with optional signal
   * @return a Promise for an array of Feature
   */
  public async searchExtraIndex(name: string, opts: RequestOptions = {}) {
    const blocks = await this.searchExtraIndexBlocks(name, opts)
    if (blocks.length === 0) {
      return []
    }
    const view = await this.getUnzoomedView(opts)
    const res = blocks.map(block => {
      return new Observable<Feature[]>(observer => {
        view.readFeatures(observer, [block], opts)
      }).pipe(
        reduce((acc, curr) => acc.concat(curr)),
        map(x => {
          for (const element of x) {
            element.field = block.field
          }
          return x
        }),
      )
    })
    const ret = await firstValueFrom(merge(...res))
    return ret.filter(f => f.rest?.split('\t')[(f.field || 0) - 3] === name)
  }
}
