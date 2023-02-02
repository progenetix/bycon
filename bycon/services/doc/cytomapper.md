## _cytomapper_ Service

This script parses either:

* a properly formatted cytoband annotation (`assemblyId`, `cytoBands`)
  - "8", "9p11q21", "8q", "1p12qter"
* a concatenated `chroBases` parameter
  - `7:23028447-45000000`
  - `X:99202660`

While the return object is JSON by default, specifying `text=1`, together with the `cytoBands` or
`chroBases` parameter will return the text version of the opposite.

There is a fallback to *GRCh38* if no assembly is being provided.

The `cytobands` and `chrobases` parameters can be used for running the script on the command line
(see examples below). Please be aware of the "chrobases" (command line) versus "chroBases" (cgi) use.

#### Examples

* retrieve coordinates for some bands on chromosome 8
  - <https://progenetix.org/services/cytomapper?assemblyId=NCBI36.1&cytoBands=8q24.1>
* as above, just as text:
  - <https://progenetix.org/services/cytomapper?assemblyId=NCBI.1&cytoBands=8q&text=1>
  - *cytomapper shortcut*: <https://progenetix.org/services/cytomapper/?assemblyId=NCBI36.1&cytoBands=8q&text=1>
* get the cytobands whith which a base range on chromosome 17 overlaps, in short and long form
  - <https://progenetix.org/services/cytomapper?assemblyId=GRCh37&chroBases=17:800000-24326000>
* using `curl` to get the text format mapping of a cytoband range, using the API `services` shortcut:
  - `curl -k https://progenetix.org/services/cytomapper?cytoBands\=8q21q24.1&assemblyId\=hg18&text\=1`
* command line version of the above
  - `bin/cytomapper.py --chrobases 17:800000-24326000 -g NCBI36`
  - `bin/cytomapper.py -b 17:800000-24326000`
  - `bin/cytomapper.py --cytobands 9p11q21 -g GRCh38`
  - `bin/cytomapper.py -c Xpterq24`

#### Response

As in other **bycon** `services`, API responses are in JSON format with the main
content being contained in the `data` field.

As of v2020-09-29, the `ChromosomeLocation` response is compatible to the [GA4GH 
VRS standard](https://vr-spec.readthedocs.io/en/1.1/terms_and_model.html#chromosomelocation).
The `GenomicLocation` object is a wrapper around a VRS `SimpleInterval`.

```
{
  "data": {
    "ChromosomeLocation": {
      "chr": "8",
      "interval": {
        "end": "q24.13",
        "start": "q24.11",
        "type": "CytobandInterval"
      },
      "species_id": "taxonomy:9606",
      "type": "ChromosomeLocation"
    },
    "GenomicLocation": {
      "chr": "8",
      "interval": {
        "end": 127300000,
        "start": 117700000,
        "type": "SimpleInterval"
      },
      "species_id": "taxonomy:9606",
      "type": "GenomicLocation"
    },
    "info": {
      "bandList": [
        "8q24.11",
        "8q24.12",
        "8q24.13"
      ],
      "chroBases": "8:117700000-127300000",
      "cytoBands": "8q24.11q24.13",
      "referenceName": "8",
      "size": 9600000
    }
  },
  "errors": [],
  "parameters": {
    "assemblyId": "NCBI36.1",
    "cytoBands": "8q24.1"
  }
}
```
