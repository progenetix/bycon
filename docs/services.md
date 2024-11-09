# Bycon <i>services</i>

The _bycon_ environment provides a number of data services beyond typical Beacon
functionality. These services can be loosely grouped into two major types:

* services which extend Beacon formats, _i.e._ use Beacon concepts and query
  parameters but provide non-standard output
    - plotting functions
    - tabular and text output
    - aggregated data such as CNV frequencies (see [_intervalFrequencies_](/bycon-services/intervalFrequencies))
* services which make use of utility function and data existing primarily for the
  support of Beacon functionality
    - ontology term cross mapping
    - geneId to location lookup
    - geographic location mapping and map projections (see [_geolocations_](/bycon-services/geolocations))
    - ISCN cytogenetic band mapping
    - publication data for cancer genome screening publications

## Available Services

The complete list of service endpoints can be found in the [services index](/generated/services).
The page also provides general information about individual service endpoints from their
embedded documentation.

## `services.py` and URL Mapping

Bycon web services are called through the `services.py` app which is installed
at the bycon server root. The system path for `services.py` is

```
{bycon_install_dir}/services/services.py
```

... where `bycon_install_dir` has to be user defined inside the `local/local_paths.yaml`
configuration file (see [Installation](/installation)). The service URL format `progenetix.org/services/__service-name__?parameter=value`
is based on the remapping of the `services.py` script to the `/services` path and
then extraction of the service name as the path parameter following `/services/`.

The functionality is combined with the correct configuration of a 
rewrite in the server configuration (see [Installation](/installation)).

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
