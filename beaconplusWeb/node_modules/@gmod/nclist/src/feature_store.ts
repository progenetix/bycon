//@ts-nocheck
import nodeUrl from 'url'
import QuickLRU from 'quick-lru'
import AbortablePromiseCache from 'abortable-promise-cache'

import GenericNCList from './nclist'
import ArrayRepr from './array_representation'
import LazyArray from './lazy_array'
import { readJSON } from './util'

function idfunc() {
  return this._uniqueID
}
function parentfunc() {
  return this._parent
}
function childrenfunc() {
  return this.get('subfeatures')
}

/**
 * Sequence feature store using nested containment
 * lists held in JSON files that are lazily read.
 *
 * @param {object} args constructor args
 * @param {string} args.baseUrl base URL for resolving relative URLs
 * @param {string} args.urlTemplate Template string for
 *  the root file of each reference sequence. The reference sequence
 *  name will be interpolated into this string where `{refseq}` appears.
 * @param {function} args.readFile function to use for reading remote from URLs.
 */
export default class NCListStore {
  constructor({ baseUrl, urlTemplate, readFile, cacheSize = 10 }) {
    this.baseUrl = baseUrl
    this.urlTemplates = { root: urlTemplate }

    this.readFile = readFile
    if (!this.readFile) {
      throw new Error(`must provide a "readFile" function argument`)
    }

    this.dataRootCache = new AbortablePromiseCache({
      cache: new QuickLRU({ maxSize: cacheSize }),
      fill: this.fetchDataRoot.bind(this),
    })
  }

  makeNCList() {
    return new GenericNCList({ readFile: this.readFile })
  }

  loadNCList(refData, trackInfo, listUrl) {
    refData.nclist.importExisting(
      trackInfo.intervals.nclist,
      refData.attrs,
      listUrl,
      trackInfo.intervals.urlTemplate,
      trackInfo.intervals.lazyClass,
    )
  }

  getDataRoot(refName) {
    return this.dataRootCache.get(refName, refName)
  }

  fetchDataRoot(refName) {
    const url = nodeUrl.resolve(
      this.baseUrl,
      this.urlTemplates.root.replace(/{\s*refseq\s*}/g, refName),
    )

    // fetch the trackdata
    return readJSON(url, this.readFile).then(trackInfo =>
      // trackInfo = JSON.parse( trackInfo );
      this.parseTrackInfo(trackInfo, url),
    )
  }

  parseTrackInfo(trackInfo, url) {
    const refData = {
      nclist: this.makeNCList(),
      stats: {
        featureCount: trackInfo.featureCount || 0,
      },
    }

    if (trackInfo.intervals) {
      refData.attrs = new ArrayRepr(trackInfo.intervals.classes)
      this.loadNCList(refData, trackInfo, url)
    }

    const { histograms } = trackInfo
    if (histograms && histograms.meta) {
      for (let i = 0; i < histograms.meta.length; i += 1) {
        histograms.meta[i].lazyArray = new LazyArray(
          { ...histograms.meta[i].arrayParams, readFile: this.readFile },
          url,
        )
      }
      refData._histograms = histograms
    }

    // parse any strings in the histogram data that look like numbers
    if (refData._histograms) {
      Object.keys(refData._histograms).forEach(key => {
        const entries = refData._histograms[key]
        entries.forEach(entry => {
          Object.keys(entry).forEach(key2 => {
            if (
              typeof entry[key2] === 'string' &&
              String(Number(entry[key2])) === entry[key2]
            ) {
              entry[key2] = Number(entry[key2])
            }
          })
        })
      })
    }

    return refData
  }

  async getRegionStats(query) {
    const data = await this.getDataRoot(query.ref)
    return data.stats
  }

  /**
   * fetch binned counts of feature coverage in the given region.
   *
   * @param {object} query
   * @param {string} query.refName reference sequence name
   * @param {number} query.start region start
   * @param {number} query.end region end
   * @param {number} query.numBins number of bins desired in the feature counts
   * @param {number} query.basesPerBin number of bp desired in each feature counting bin
   * @returns {object} as:
   *    `{ bins: hist, stats: statEntry }`
   */
  async getRegionFeatureDensities({
    refName,
    start,
    end,
    numBins,
    basesPerBin,
  }) {
    const data = await this.getDataRoot(refName)
    if (numBins) {
      basesPerBin = (end - start) / numBins
    } else if (basesPerBin) {
      numBins = Math.ceil((end - start) / basesPerBin)
    } else {
      throw new TypeError(
        'numBins or basesPerBin arg required for getRegionFeatureDensities',
      )
    }

    // pick the relevant entry in our pre-calculated stats
    const stats = data._histograms.stats || []
    const statEntry = stats.find(entry => entry.basesPerBin >= basesPerBin)

    // The histogramMeta array describes multiple levels of histogram detail,
    // going from the finest (smallest number of bases per bin) to the
    // coarsest (largest number of bases per bin).
    // We want to use coarsest histogramMeta that's at least as fine as the
    // one we're currently rendering.
    // TODO: take into account that the histogramMeta chosen here might not
    // fit neatly into the current histogram (e.g., if the current histogram
    // is at 50,000 bases/bin, and we have server histograms at 20,000
    // and 2,000 bases/bin, then we should choose the 2,000 histogramMeta
    // rather than the 20,000)
    let histogramMeta = data._histograms.meta[0]
    for (let i = 0; i < data._histograms.meta.length; i += 1) {
      if (basesPerBin >= data._histograms.meta[i].basesPerBin) {
        histogramMeta = data._histograms.meta[i]
      }
    }

    // number of bins in the server-supplied histogram for each current bin
    let binRatio = basesPerBin / histogramMeta.basesPerBin

    // if the server-supplied histogram fits neatly into our requested
    if (binRatio > 0.9 && Math.abs(binRatio - Math.round(binRatio)) < 0.0001) {
      // console.log('server-supplied',query);
      // we can use the server-supplied counts
      const firstServerBin = Math.floor(start / histogramMeta.basesPerBin)
      binRatio = Math.round(binRatio)
      const histogram = []
      for (let bin = 0; bin < numBins; bin += 1) {
        histogram[bin] = 0
      }

      for await (const [i, val] of histogramMeta.lazyArray.range(
        firstServerBin,
        firstServerBin + binRatio * numBins - 1,
      )) {
        // this will count features that span the boundaries of
        // the original histogram multiple times, so it's not
        // perfectly quantitative.  Hopefully it's still useful, though.
        histogram[Math.floor((i - firstServerBin) / binRatio)] += val
      }
      return { bins: histogram, stats: statEntry }
    }
    // console.log('make own',query);
    // make our own counts
    const hist = await data.nclist.histogram(start, end, numBins)
    return { bins: hist, stats: statEntry }
  }

  /**
   * Fetch features in a given region. This method is an asynchronous generator
   * yielding feature objects.
   *
   * @param {object} args
   * @param {string} args.refName reference sequence name
   * @param {number} args.start start of region. 0-based half-open.
   * @param {number} args.end end of region. 0-based half-open.
   * @yields {object}
   */
  async *getFeatures({ refName, start, end }) {
    const data = await this.getDataRoot(refName)
    const accessors = data.attrs && data.attrs.accessors()
    for await (const [feature, path] of data.nclist.iterate(start, end)) {
      // the unique ID is a stringification of the path in the
      // NCList where the feature lives; it's unique across the
      // top-level NCList (the top-level NCList covers a
      // track/chromosome combination)

      // only need to decorate a feature once
      if (!feature.decorated) {
        const uniqueID = path.join(',')
        this.decorateFeature(accessors, feature, `${refName},${uniqueID}`)
      }
      yield feature
    }
  }

  // helper method to recursively add .get and .tags methods to a feature and its
  // subfeatures
  decorateFeature(accessors, feature, id, parent) {
    feature.get = accessors.get
    feature.tags = accessors.tags
    feature._uniqueID = id
    feature.id = idfunc
    feature._parent = parent
    feature.parent = parentfunc
    feature.children = childrenfunc
    ;(feature.get('subfeatures') || []).forEach((f, i) => {
      this.decorateFeature(accessors, f, `${id}-${i}`, feature)
    })
    feature.decorated = true
  }
}
