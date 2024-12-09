![Build Status](https://img.shields.io/github/actions/workflow/status/GMOD/trix-js/push.yml?branch=main)

# trix-js

Read UCSC Trix indexes in pure JavaScript

## Usage

```js
import Trix from '@gmod/trix'
import { RemoteFile } from 'generic-filehandle'

// any filehandle object that supports the Nodejs FileHandle API will work.
// We use generic-filehandle here to demonstrate searching files on remote servers.
const ixxFile = new RemoteFile(
  'https://hgdownload.soe.ucsc.edu/gbdb/hg38/knownGene.ixx',
)
const ixFile = new RemoteFile(
  'https://hgdownload.soe.ucsc.edu/gbdb/hg38/knownGene.ix',
)

const trix = new Trix(ixxFile, ixFile)

async function doStuff() {
  const results = await trix.search('oca')
  console.log(results)
}
doStuff()
```

## Documentation

### Trix constructor

The Trix class constructor accepts arguments:

- `ixxFile` - a filehandle object for the trix .ixx file
- `ixFile` - a filehandle object for the trix .ix file
- `maxResults = 20` - an optional number specifying the maximum number of results to return on `trix.search()`

### Trix search

**Search the index files for a term and find its keys.**<br>
**In the case of searching with multiple words, `trix.search()` finds the intersection of the result sets.**<br>
The Trix search function accepts argument:

- `searchString` - a string of space-separated words for what to search the index file and find keys for<br>

The Trix search function returns: <br>

- `Promise<[term,result][] as [string,string][]>` - an array of [term, result] pairs where each term is the left column in the trix and the right column is the trix match

## Examples

```js
import { LocalFile } from 'generic-filehandle'
import Trix from '@gmod/trix'

const ixxFile = new LocalFile('out.ixx')
const ixFile = new LocalFile('out.ix')

// limit maxResults to 5
const trix = new Trix(ixxFile, ixFile, 5)

async function doStuff() {
  const results1 = await trix.search('herc')
  console.log(results1)

  // increase maxResults to 30
  trix.maxResults = 30

  const results2 = await trix.search('linc')
  console.log(results2)
}

doStuff()
```

<br><br>

## Development

### Test trix-js

First, clone this repo and install npm packages. <br>
Then, run `npm test`. <br>

### Test the USCS TrixSearch - Requires Linux

First, clone this repo.
To run test searches on a track hub using the USCS `TrixSearch`, navigate to `tests/testdata/test#` and run `bash test#script.sh` where # is the test number.
To change search terms, edit `searchterms.txt`.

**Wondering what to search for?**<br>
Open up `tests/testdata/test#/input.txt`.

**How to test my own .gff.gz data?**<br>
Navigate to `/test/rawGenomes` and create a directory with your .gff.gz file in it. From within that directory, run `bash ../../programs/gff3ToInput.sh <.gff3.gz FILE> <OUTPUT NAME>`.

## Reference

See https://genome.ucsc.edu/goldenPath/help/trix.html for basic concepts of trix and https://github.com/GMOD/ixixx-js for a javascript implementation of the ixIxx command
