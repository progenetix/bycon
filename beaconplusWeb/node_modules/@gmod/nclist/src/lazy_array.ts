//@ts-nocheck
import nodeUrl from 'url'
import QuickLRU from 'quick-lru'
import AbortablePromiseCache from 'abortable-promise-cache'
import { readJSON } from './util'

/**
 * For a JSON array that gets too large to load in one go, this class
 * helps break it up into chunks and provides an
 * async API for using the information in the array.
 */
export default class LazyArray {
  constructor(
    { urlTemplate, chunkSize, length, cacheSize = 100, readFile },
    baseUrl,
  ) {
    this.urlTemplate = urlTemplate
    this.chunkSize = chunkSize
    this.length = length
    this.baseUrl = baseUrl === undefined ? '' : baseUrl
    this.readFile = readFile
    if (!readFile) {
      throw new Error('must provide readFile callback')
    }
    this.chunkCache = new AbortablePromiseCache({
      cache: new QuickLRU({ maxSize: cacheSize }),
      fill: this.getChunk.bind(this),
    })
  }

  /**
   * call the callback on one element of the array
   * @param i index
   * @param callback callback, gets called with (i, value, param)
   * @param param (optional) callback will get this as its last parameter
   */
  index(i, callback, param) {
    this.range(i, i, callback, undefined, param)
  }

  /**
   * async generator for the elements in the range [start,end]
   *
   * @param start index of first element to call the callback on
   * @param end index of last element to call the callback on
   */
  async *range(start, end) {
    start = Math.max(0, start)
    end = Math.min(end, this.length - 1)

    const firstChunk = Math.floor(start / this.chunkSize)
    const lastChunk = Math.floor(end / this.chunkSize)

    const chunkreadFiles = []
    for (let chunk = firstChunk; chunk <= lastChunk; chunk += 1) {
      chunkreadFiles.push(this.chunkCache.get(chunk, chunk))
    }
    for (let i = 0; i < chunkreadFiles.length; i += 1) {
      const [chunkNumber, chunkData] = await chunkreadFiles[i]
      yield* this.filterChunkData(start, end, chunkNumber, chunkData)
    }
  }

  async getChunk(chunkNumber) {
    let url = this.urlTemplate.replace(/\{Chunk\}/gi, chunkNumber)
    if (this.baseUrl) {
      url = nodeUrl.resolve(this.baseUrl, url)
    }
    const data = await readJSON(url, this.readFile)
    return [chunkNumber, data]
  }

  *filterChunkData(queryStart, queryEnd, chunkNumber, chunkData) {
    // index (in the overall lazy array) of the first position in this chunk
    const firstIndex = chunkNumber * this.chunkSize
    const chunkStart = Math.max(0, queryStart - firstIndex)
    const chunkEnd = Math.min(queryEnd - firstIndex, this.chunkSize - 1)
    for (let i = chunkStart; i <= chunkEnd; i += 1) {
      yield [i + firstIndex, chunkData[i]]
    }
  }
}
