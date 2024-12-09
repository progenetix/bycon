# bbi-js

[![NPM version](https://img.shields.io/npm/v/@gmod/bbi.svg?style=flat-square)](https://npmjs.org/package/@gmod/bbi)
[![Coverage Status](https://img.shields.io/codecov/c/github/GMOD/bbi-js/master.svg?style=flat-square)](https://codecov.io/gh/GMOD/bbi-js/branch/master)
[![Build Status](https://img.shields.io/github/actions/workflow/status/GMOD/bbi-js/push.yml?branch=master)](https://github.com/GMOD/bbi-js/actions?query=branch%3Amaster+workflow%3APush+)

A parser for bigwig and bigbed file formats

## Usage

If using locally

```typescript
const { BigWig } = require('@gmod/bbi')
const file = new BigWig({
  path: 'volvox.bw',
})
;(async () => {
  await file.getHeader()
  const feats = await file.getFeatures('chr1', 0, 100, { scale: 1 })
})()
```

If using remotely, you can use it in combination with generic-filehandle or your
own implementation of something like generic-filehandle
https://github.com/GMOD/generic-filehandle/

```typescript
const { BigWig } = require('@gmod/bbi')
const { RemoteFile } = require('generic-filehandle')

// if running in the browser or newer versions of node.js, RemoteFile will use
// the the global fetch
const file = new BigWig({
  filehandle: new RemoteFile('volvox.bw'),
})

// old versions of node.js without a global fetch, supply custom fetch function
const fetch = require('node-fetch')
const file = new BigWig({
  filehandle: new RemoteFile('volvox.bw', { fetch }),
})

;(async () => {
  await file.getHeader()
  const feats = await file.getFeatures('chr1', 0, 100, { scale: 1 })
})()
```

## Documentation

### BigWig/BigBed constructors

Accepts an object containing either

- path - path to a local file
- url - path to a url
- filehandle - a filehandle instance that you can implement as a custom class
  yourself. path and url are based on
  https://www.npmjs.com/package/generic-filehandle but by implementing a class
  containing the Filehandle interface specified therein, you can pass it to this
  module

### BigWig

#### getFeatures(refName, start, end, opts)

- refName - a name of a chromosome in the file
- start - a 0-based half open start coordinate
- end - a 0-based half open end coordinate
- opts.scale - indicates zoom level to use, specified as pxPerBp, e.g. being
  zoomed out, you might have 100bp per pixel so opts.scale would be 1/100. the
  zoom level that is returned is the one which has reductionLevel<=2/opts.scale
  (reductionLevel is a property of the zoom level structure in the bigwig file
  data)
- opts.basesPerScale - optional, inverse of opts.scale e.g. bpPerPx
- opts.signal - optional, an AbortSignal to halt processing

Returns a promise to an array of features. If an incorrect refName or no
features are found the result is an empty array.

Example:

```typescript
const feats = await bigwig.getFeatures('chr1', 0, 100)
// returns array of features with start, end, score
// coordinates on returned data are are 0-based half open
// no conversion to 1-based as in wig is done)
// note refseq is not returned on the object, it is clearly chr1 from the query though
```

### Understanding scale and reductionLevel

Here is what the reductionLevel structure looks like in a file. The zoomLevel
that is chosen is the first reductionLevel<2\*opts.basesPerScale (or
reductionLevel<2/opts.scale) when scanning backwards through this list

      [ { reductionLevel: 40, ... },
        { reductionLevel: 160, ... },
        { reductionLevel: 640, ... },
        { reductionLevel: 2560, ... },
        { reductionLevel: 10240, ... },
        { reductionLevel: 40960, ... },
        { reductionLevel: 163840, ... } ]

#### getFeatureStream(refName, start, end, opts)

Same as getFeatures but returns an RxJS observable stream, useful for very large
queries

```typescript
const observer = await bigwig.getFeatureStream('chr1', 0, 100)
observer.subscribe(
  chunk => {
    /* chunk contains array of features with start, end, score */
  },
  error => {
    /* process error */
  },
  () => {
    /* completed */
  },
)
```

### BigBed

#### getFeatures(refName, start, end, opts)

- refName - a name of a chromosome in the file
- start - a 0-based half open start coordinate
- end - a 0-based half open end coordinate
- opts.signal - optional, an AbortSignal to halt processing

returns a promise to an array of features. no concept of zoom levels is used
with bigwig data

#### getFeatureStream(refName, start, end, opts)

Similar to BigWig, returns an RxJS observable for a observable stream

#### searchExtraIndex(name, opts)

Specific, to bigbed files, this method searches the bigBed "extra indexes",
there can be multiple indexes e.g. for the gene ID and gene name columns. See
the usage of -extraIndex in bedToBigBed here
https://genome.ucsc.edu/goldenpath/help/bigBed.html

This function accepts two arguments

- name: a string to search for in the BigBed extra indices
- opts: an object that can optionally contain opts.signal, an abort signal

Returns a Promise to an array of Features, with an extra field indicating the
field that was matched

### How to parse BigBed results

The BigBed line contents are returned as a raw text line e.g. {start: 0,
end:100, rest: "ENST00000456328.2\t1000\t..."} where "rest" contains tab
delimited text for the fields from 4 and on in the BED format. Since BED files
from BigBed format often come with autoSql (a description of all the columns) it
can be useful to parse it with BED parser that can handle autoSql. The rest line
can be parsed by the @gmod/bed module, which is not by default integrated with
this module, but can be combined with it as follows

```typescript
import { BigBed } from '@gmod/bbi'
import BED from '@gmod/bed'

const ti = new BigBed({
  filehandle: new LocalFile(require.resolve('./data/hg18.bb')),
})
const { autoSql } = await ti.getHeader()
const feats = await ti.getFeatures('chr7', 0, 100000)
const parser = new BED({ autoSql })
const lines = feats.map(f => {
  const { start, end, rest, uniqueId } = f
  return parser.parseLine(`chr7\t${start}\t${end}\t${rest}`, { uniqueId })
})
// @gmod/bbi returns features with {uniqueId, start, end, rest}
// we reconstitute this as a line for @gmod/bed with a template string
// note: the uniqueId is based on file offsets and helps to deduplicate exact feature copies if they exist
```

Features before parsing with @gmod/bed:

```json
{
  "chromId": 0,
  "start": 64068,
  "end": 64107,
  "rest": "uc003sil.1\t0\t-\t64068\t64068\t255,0,0\t.\tDQ584609",
  "uniqueId": "bb-171"
}
```

Features after parsing with @gmod/bed:

```json
{
  "uniqueId": "bb-0",
  "chrom": "chr7",
  "chromStart": 54028,
  "chromEnd": 73584,
  "name": "uc003sii.2",
  "score": 0,
  "strand": -1,
  "thickStart": 54028,
  "thickEnd": 54028,
  "reserved": "255,0,0",
  "spID": "AL137655"
}
```

## Academic Use

This package was written with funding from the [NHGRI](http://genome.gov) as
part of the [JBrowse](http://jbrowse.org) project. If you use it in an academic
project that you publish, please cite the most recent JBrowse paper, which will
be linked from [jbrowse.org](http://jbrowse.org).

## License

MIT © [Colin Diesh](https://github.com/cmdcolin)
