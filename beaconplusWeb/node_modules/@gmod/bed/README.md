# bed-js

[![Coverage Status](https://img.shields.io/codecov/c/github/GMOD/bed-js/master.svg?style=flat-square)](https://codecov.io/gh/GMOD/bed-js/branch/master)
[![Build Status](https://img.shields.io/github/actions/workflow/status/GMOD/bed-js/push.yml?branch=master)](https://github.com/GMOD/bed-js/actions)

Performs parsing of BED files including autoSql

## Usage

### Example

You can pipe your file through this programs parseLine function

```js
import BED from '@gmod/bed'

// you might require compatibility with node.js to use the default export with require e.g.
// const BED = require('@gmod/bed').default

var parser = new BED()
var text = fs.readFileSync('file.txt', 'utf8')
var results = text.split('\n').map(line => parser.parseLine(line))
```

## API

### Constructor

The BED constructor accepts an opts object with options

- opts.autoSql - a optional autoSql schema for parsing lines
- opts.type - a string representing one of a list of predefined types

The predefined types can include

    bigInteract
    bigMaf
    bigPsl
    bigNarrowPeak
    bigGenePred
    bigLink
    bigChain
    mafFrames
    mafSummary

If neither autoSql or type is specified, the default BED schema is used (see
[here](src/as/defaultBedSchema.as))

### parseLine(line, opts)

Parses a BED line according to the currently loaded schema

- line: `string|Array<string>` - is a tab delimited line with fields from the
  schema, or an array that has been pre-split by tab with those same contents
- opts: Options - an options object

An Options object can contain

- opts.uniqueId - an indication of a uniqueId that is not encoded by the BED
  line itself

The default instantiation of the parser with new BED() simply parses lines
assuming the fields come from the standard BED schema. Your line can just
contain just a subset of the fields e.g.
`chrom, chromStart, chromEnd, name, score`

## Examples

### Parsing BED with default schema

```js
const p = new BED()

p.parseLine('chr1\t0\t100')
// outputs { chrom: 'chr1', chromStart: 0, chromEnd: 100, strand: 0 }
```

### Parsing BED with a built in schema e.g. bigGenePred

If you have a BED format that corresponds to a different schema, you can specify
from the list of default built in schemas

Specify this in the opts.type for the BED constructor

```js
const p = new BED({ type: 'bigGenePred' })
const line = 'chr1\t11868\t14409\tENST00000456328.2\t1000\t+\t11868\t11868\t255,128,0\t3\t359,109,1189,\t0,744,1352,\tDDX11L1\tnone\tnone\t-1,-1,-1,\tnone\tENST00000456328.2\tDDX11L1\tnone'
p.parseLine(line)
// above line outputs
      { chrom: 'chr1',
        chromStart: 11868,
        chromEnd: 14409,
        name: 'ENST00000456328.2',
        score: 1000,
        strand: 1,
        thickStart: 11868,
        thickEnd: 11868,
        reserved: '255,128,0',
        blockCount: 3,
        blockSizes: [ 359, 109, 1189 ],
        chromStarts: [ 0, 744, 1352 ],
        name2: 'DDX11L1',
        cdsStartStat: 'none',
        cdsEndStat: 'none',
        exonFrames: [ -1, -1, -1 ],
        type: 'none',
        geneName: 'ENST00000456328.2',
        geneName2: 'DDX11L1',
        geneType: 'none' }
```

### Parsing BED with a supplied autoSql

If you have a BED format with a custom alternative schema with autoSql, or if
you are using a BigBed file that contains autoSql (e.g. with
[@gmod/bbi](https://github.com/gmod/bbi-js) then you can get it from
header.autoSql) then you initialize the schema in the constructor and then use
parseLine as normal

```
const {BigBed} = require('@gmod/bbi')
const bigbed = new BigBed({path: 'yourfile'})
const {autoSql} = await bigbed.getHeader()
const p = new BED({ autoSql })
p.parseLine(line)
// etc.
```

### Important notes

- Does not parse "browser" or "track" lines and will throw an error if parseLine
  receives one of these
- By default, parseLine parses only tab delimited text, if you want to use
  spaces as is allowed by UCSC then pass an array to `line` for parseLine
- Converts strand from {+,-,.} to {1,-1,0} and also sets strand 0 even if no
  strand is in the autoSql

## Academic Use

This package was written with funding from the [NHGRI](http://genome.gov) as
part of the [JBrowse](http://jbrowse.org) project. If you use it in an academic
project that you publish, please cite the most recent JBrowse paper, which will
be linked from [jbrowse.org](http://jbrowse.org).

## License

MIT © [Colin Diesh](https://github.com/cmdcolin)

based on
https://genome-source.gi.ucsc.edu/gitlist/kent.git/blob/master/src/hg/autoSql/autoSql.doc

also see http://genomewiki.ucsc.edu/index.php/AutoSql and
https://www.linuxjournal.com/article/5949
