//@ts-nocheck
export function parseCacheControl(field) {
  if (typeof field !== 'string') {
    return {}
  }

  const parsed = {}
  const invalid = field.toLowerCase().replace(
    // eslint-disable-next-line no-control-regex,no-useless-escape
    /(?:^|(?:\s*,\s*))([^\x00-\x20\(\)<>@\,;\:\\"\/\[\]\?\=\{\}\x7F]+)(?:\=(?:([^\x00-\x20\(\)<>@\,;\:\\"\/\[\]\?\=\{\}\x7F]+)|(?:\"((?:[^"\\]|\\.)*)\")))?/g,
    (match, fieldName, three, four) => {
      const value = three || four
      parsed[fieldName] = value ? value.toLowerCase() : true
      return ''
    },
  )

  if (invalid) {
    return {}
  }

  // parse any things that seem to be numbers
  Object.keys(parsed).forEach(key => {
    if (/^[\d]+$/.test(parsed[key])) {
      try {
        const num = parseInt(parsed[key], 10)
        if (!Number.isNaN(num)) {
          parsed[key] = num
        }
      } catch (e) {
        /* ignore */
      }
    }
  })

  return parsed
}

export class CacheSemantics {
  constructor({ minimumTTL }) {
    this.minimumTTL = minimumTTL
  }

  calculateChunkExpirationDate(chunkResponse) {
    const { headers = {}, requestDate, responseDate } = chunkResponse
    let baselineDate = responseDate || requestDate
    if (!baselineDate) {
      if (!headers.date) {
        return undefined
      }
      baselineDate = new Date(headers.date)
    }

    const basePlus = ttl => new Date(baselineDate.getTime() + ttl)

    // results that are not really cacheable expire after the minimum time to live
    if (/\bno-cache\b/.test(headers.pragma)) {
      return basePlus(this.minimumTTL)
    }

    const cacheControl = parseCacheControl(headers['cache-control'])
    if (
      cacheControl['no-cache'] ||
      cacheControl['no-store'] ||
      cacheControl['must-revalidate']
    ) {
      return basePlus(this.minimumTTL)
    }

    if (cacheControl['max-age'] !== undefined) {
      const ttl = cacheControl['max-age'] * 1000 // max-age is in seconds
      return basePlus(Math.max(ttl, this.minimumTTL))
    } else if (this._coerceToDate(headers.expires)) {
      return this._coerceToDate(headers.expires)
    } else if (this._coerceToDate(headers['last-modified'])) {
      const lastModified = this._coerceToDate(headers['last-modified'])
      const ttl = (baselineDate.getTime() - lastModified.getTime()) / 10
      return basePlus(ttl)
    }

    // otherwise, we just cache forever
    return undefined
  }

  _coerceToDate(thing) {
    if (thing) {
      if (thing instanceof Date) {
        return thing
      }
      if (typeof thing === 'string' || typeof thing === 'number') {
        return new Date(thing)
      }
    }
    return undefined
  }

  /**
   * check whether a cached chunk response is still valid and can be used
   * @param {object} chunkResponse
   * @returns {boolean}
   */
  cachedChunkIsValid(chunkResponse) {
    const expiration = this.calculateChunkExpirationDate(chunkResponse)
    return !expiration || new Date() <= expiration
  }

  /**
   * check whether the response for this chunk fetch can be cached
   * @param {object} chunkResponse
   * @returns {boolean}
   */
  chunkIsCacheable() {
    // right now, we are caching everything, we just give it a very short
    // time to live if it's not supposed to be cached
    return true
  }
}
