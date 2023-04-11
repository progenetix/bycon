---
title: Bycon <i>services</i>
---

The _bycon_ environment provides a number of data services which make use of
resources in the _Progenetix_ environment. Please refer to their specific
documentation.

* [_collations_](collations.md)
* [_cytomapper_](cytomapper.md)
* [_genespans_](genespans.md)
* [_geolocations_](geolocations.md)
* [_intervalFrequencies_](intervalFrequencies.md)
* [_ids_](ids.md)
* [_publications_](publications.md)

## `services.py` and URL Mapping

The service URL format `progenetix.org/services/__service-name__?parameter=value`
is a shorthand for `progenetix.org/cgi-bin/bycon/services/__service-name__.py?parameter=value`.

The `services` application deparses a request URI and calls the respective
script. The functionality is combined with the correct configuration of a 
rewrite in the server configuration (Apache example):

```
RewriteRule "^/services(.*)"    /cgi-bin/bycon/services/services.py$1   [PT]
```

## Response formats

Standard responses are provided as `Content-Type: application/json`. The wrapper
format is based on the Beacon v2 response format, with the data returned in the
`results` array: 

```
meta:
  api_version: ...
  returned_schemas: [ ]
response:
  exists: true | false
  info: { }
  resultSets: [ ]
```

This (incomplete) example response may help with understanding the general
format. Here, the data is a dictionary/object with a single key (`genes`):

#### Request  Example

* <https://progenetix.org/services/genespans?geneId=CDKN2>

#### Response Example

```json
{
  "meta": {
    "apiVersion": "v2.1.0-beaconplus",
    "beaconId": "org.progenetix",
    "___more_parameters___": {},
    "info": "The main genes payload can be accessed in `response.results`.\n",
    "testMode": false
  },
  "response": {
    "results": [
      {
        "accessionVersion": "NC_000012.12",
        "annotations": [
          {
            "assembliesInScope": [
              {
                "accession": "GCF_000001405.39",
                "name": "GRCh38.p13"
              }
            ],
            "releaseDate": "2021-05-14",
            "releaseName": "NCBI Homo sapiens Updated Annotation Release 109.20210514"
          }
        ],
        "cytobands": "12q13.2",
        "end": 55972789,
        "ensemblGeneIds": [
          "ENSG00000123374"
        ],
        "geneId": "1017",
        "geneLocusLength": 5959,
        "genomicRanges": [
          {
            "accessionVersion": "NC_000012.12",
            "range": [
              {
                "begin": "55966830",
                "end": "55972789",
                "order": null,
                "orientation": "plus",
                "ribosomalSlippage": null
              }
            ]
          }
        ],
        "nomenclatureAuthority": {
          "authority": "HGNC",
          "identifier": "HGNC:1771"
        },
        "omimIds": [
          "116953"
        ],
        "orientation": "plus",
        "referenceName": "12",
        "start": 55966830,
        "swissProtAccessions": [
          "P24941"
        ],
        "symbol": "CDK2",
        "synonyms": [
          "CDKN2",
          "p33(CDK2)"
        ],
        "type": "PROTEIN_CODING"
      },
      {"___more___"}
    ]
  }
}
```
