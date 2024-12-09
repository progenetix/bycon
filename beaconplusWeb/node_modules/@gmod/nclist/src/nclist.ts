//@ts-nocheck
import nodeUrl from 'url'
import QuickLRU from 'quick-lru'
import AbortablePromiseCache from 'abortable-promise-cache'
import { readJSON } from './util'

export default class NCList {
  constructor({ readFile, cacheSize = 100 }) {
    this.topList = []
    this.chunkCache = new AbortablePromiseCache({
      cache: new QuickLRU({ maxSize: cacheSize }),
      fill: this.readChunkItems.bind(this),
    })
    this.readFile = readFile
    if (!this.readFile) {
      throw new Error(`must provide a "readFile" function`)
    }
  }

  importExisting(nclist, attrs, baseURL, lazyUrlTemplate, lazyClass) {
    this.topList = nclist
    this.attrs = attrs
    this.start = attrs.makeFastGetter('Start')
    this.end = attrs.makeFastGetter('End')
    this.lazyClass = lazyClass
    this.baseURL = baseURL
    this.lazyUrlTemplate = lazyUrlTemplate
  }

  binarySearch(arr, item, getter) {
    let low = -1
    let high = arr.length
    let mid

    while (high - low > 1) {
      mid = (low + high) >>> 1
      if (getter(arr[mid]) >= item) {
        high = mid
      } else {
        low = mid
      }
    }

    // if we're iterating rightward, return the high index;
    // if leftward, the low index
    if (getter === this.end) {
      return high
    }
    return low
  }

  readChunkItems(chunkNum) {
    const url = nodeUrl.resolve(
      this.baseURL,
      this.lazyUrlTemplate.replace(/\{Chunk\}/gi, chunkNum),
    )
    return readJSON(url, this.readFile, { defaultContent: [] })
  }

  async *iterateSublist(arr, from, to, inc, searchGet, testGet, path) {
    const getChunk = this.attrs.makeGetter('Chunk')
    const getSublist = this.attrs.makeGetter('Sublist')

    const pendingPromises = []
    for (
      let i = this.binarySearch(arr, from, searchGet);
      i < arr.length && i >= 0 && inc * testGet(arr[i]) < inc * to;
      i += inc
    ) {
      if (arr[i][0] === this.lazyClass) {
        // this is a lazily-loaded chunk of the nclist
        const chunkNum = getChunk(arr[i])
        const chunkItemsP = this.chunkCache
          .get(chunkNum, chunkNum)
          .then(item => [item, chunkNum])
        pendingPromises.push(chunkItemsP)
      } else {
        // this is just a regular feature
        yield [arr[i], path.concat(i)]
      }

      // if this node has a contained sublist, process that too
      const sublist = getSublist(arr[i])
      if (sublist) {
        yield* this.iterateSublist(
          sublist,
          from,
          to,
          inc,
          searchGet,
          testGet,
          path.concat(i),
        )
      }
    }

    for (let i = 0; i < pendingPromises.length; i += 1) {
      const [item, chunkNum] = await pendingPromises[i]
      if (item) {
        yield* this.iterateSublist(item, from, to, inc, searchGet, testGet, [
          ...path,
          chunkNum,
        ])
      }
    }
  }

  async *iterate(from, to) {
    // calls the given function once for each of the
    // intervals that overlap the given interval
    // if from <= to, iterates left-to-right, otherwise iterates right-to-left

    // inc: iterate leftward or rightward
    const inc = from > to ? -1 : 1
    // searchGet: search on start or end
    const searchGet = from > to ? this.start : this.end
    // testGet: test on start or end
    const testGet = from > to ? this.end : this.start

    if (this.topList.length > 0) {
      yield* this.iterateSublist(
        this.topList,
        from,
        to,
        inc,
        searchGet,
        testGet,
        [0],
      )
    }
  }

  async histogram(from, to, numBins) {
    // calls callback with a histogram of the feature density
    // in the given interval

    const result = new Array(numBins)
    result.fill(0)
    const binWidth = (to - from) / numBins
    for await (const feat of this.iterate(from, to)) {
      const firstBin = Math.max(0, ((this.start(feat) - from) / binWidth) | 0)
      const lastBin = Math.min(
        numBins,
        ((this.end(feat) - from) / binWidth) | 0,
      )
      for (let bin = firstBin; bin <= lastBin; bin += 1) {
        result[bin] += 1
      }
    }
    return result
  }
}
