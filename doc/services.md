<!--podmd-->
## Bycon _services_

The _bycon_ environment provides a number of data services which make use of
resources in the _Progenetix_ environment.

### [_biosamples_](biosamples.md)

This endpoint is mostly aimed at providing _biosamples_ handover functionality. 
However, the app uses the same query processing mechanism as the main _byconplus_
application.

##### Examples

* <http://progenetix.org/services/biosamples?datasetIds=progenetix&assemblyId=GRCh38&includeDatasetResonses=ALL&requestType=null&referenceName=null&filterLogic=OR&filters=NCIT:C7376&filters=NCIT:C45665&filters=NCIT:C45655&filters=NCIT:C45655>

### [_collations_](collations.md)

* provides access to information about data "subsets" in the Progenetix project
databases
  - typically aggregations of samples sharing an ontology code (e.g. NCIT) or 
  external identifier (e.g. PMID)

### _publications_

* queries the _publications_ database & returns concise or extended information
about the matched articles
* currently queries are for PMID matches, genome analysis numbers and
geographic proximity; text queries are not (yet) implemented

##### Examples

* <https://progenetix.org/services/publications/?filters=PMID>
* <http://progenetix.org/cgi/bycon/bin/publications.py?filters=PMID,genomes:&gt;200,arraymap:&gt;1&method=counts>
* <http://progenetix.org/cgi/bycon/bin/publications.py?filters=PMID:22824167&method=details>
* <http://progenetix.org/cgi/bycon/bin/publications.py?geolongitude=8.55&geolatitude=47.37&geodistance=100000>

### [_cytomapper_](cytomapper.md)

* provides mappings from genome coordinates to cytobands an vice versa

##### Examples

* <https://progenetix.org/services/cytomapper?assemblyId=NCBI36.1&cytoBands=8q>
* <https://progenetix.org/services/cytomapper?cytoBands=8q21q24.1&assemblyId=hg18>
* <https://progenetix.org/services/cytomapper?chroBases=17:800000-24326000>

### _genespans_

* genomic mappings of gene coordinats
* initially limited to _GRCh38_ and overall CDS extension
* responds to (start-anchored) text input of HUGO gene symbols using the `geneId`
parameter
* returns a list of matching gene objects (see below under __Response Formats__)

##### Examples

* <https://progenetix.org/services/genespans?geneId=CDKN2>

### _geolocations_

This service provides geographic location mapping for cities above 25'000
inhabitants (\~22750 cities), through either:

* matching of the (start-anchored) name
* providing GeoJSON compatible parameters:
  - `geolongitude`
  - `geolatitude`
  - `geodistance`
    * optional, in meters; a default of 10'000m (10km) is provided
    * can be used for e.g. retrieving all places (or data from places if used
    with publication or sample searches) in an approximate region (e.g. for
    Europe using `2500000` around Heidelberg...)

##### Examples

* <https://progenetix.org/services/geolocations?city=zurich>
* <https://progenetix.org/services/geolocations?city=Heidelberg&callback=75gytk44r4yssls8j>
* <https://progenetix.org/services/geolocations?city=New&responseFormat=simplelist>
* <https://progenetix.org/services/geolocations?geolongitude=-0.13&geolatitude=51.51&geodistance=100000>


## Internal helper services

### _deliveries_

* a simple app which only provides data deliveries from handover objects
* requires a (locally existing) `accessid` parameter
* optionally limiting the response content by supplying a `deliveryKeys` list
(can be comma-concatenated or multiple times parameter)

##### Examples

Examples here need a locally existing `accessid` parameter. The context of the data
(e.g. "biosamples") is provided from the retrieved data object itself and not
apparent from the request.

* <http://progenetix.org/services/deliveries?accessid=003d0488-0b79-4ffa-a38f-2fb932480eee&deliveryKeys=id,biocharacteristics>

The response in this example was a `biosamples` dataset (excerpt):

```json
{
    "data": {
        "biosamples": [
            {
                "id": "PGX_AM_BS_20164920_SM-11YB",
                "biocharacteristics": [
                    {
                        "description": "non-small cell lung carcinoma [cell line H23]",
                        "type": {
                            "id": "icdot-C34.9",
                            "label": "lung and bronchus"
                        }

    }]}]},
 
    "errors": [],
    "parameters": {
        "accessid": "003d0488-0b79-4ffa-a38f-2fb932480eee",
        "collection": "biosamples",
        "datasetId": "progenetix"
    },
    "warnings": []
}
```

### URL Mapping

The service URL format `progenetix.org/services/__service-name__?parameter=value`
is a shorthand for `progenetix.org/cgi-bin/bycon/bin/__service-name__.py?parameter=value`.

The `services` application deparses a request URI and calls the respective
script. The functionality is combined with the correct configuration of a 
rewrite in the server configuration:

```
RewriteRule     "^/services(.*)"     /cgi-bin/bycon/bin/services.py$1      [PT]
```

### Callback handling

The JSON response (see below) will be wrapped in a callback function if a `callback` 
parameter is provided e.g. for Ajax functionality.

* <http://progenetix.org/services/collations?filters=PMID&datasetIds=progenetix&method=counts&callback=4445-9938-cbat-9891-kllt>

### Response formats

Standard responses are provided as `Content-Type: application/json`. The wrapper
format, as defined in the cofigurartion (`config/config.yaml`) provides a `data`
root parameter:

```
response_object_schema:
  parameters: { }
  data: { }
  errors: [ ]
  warnings: [ ]
```

This (incomplete) example response may help with understanding the general
format. Here, the data is a dictionary/object with a single key (`genes`):

##### Request  Example

* <https://progenetix.org/services/genespans?geneId=CDKN2>

##### Response Example

```
{
    "parameters": {
        "assemblyId": "GRCh38",
        "geneId": "CDKN2A"
    },
    "data": {
        "genes": [
            {
                "cds_end_max": 21994330,
                "cds_start_min": 21968228,
                "gene_entrez_id": 1029,
                "gene_symbol": "CDKN2A",
                "reference_name": "9"
            },
            {
                "cds_end_max": 183447426,
                "cds_start_min": 183444797,
                "gene_entrez_id": 55602,
                "gene_symbol": "CDKN2AIP",
                "reference_name": "4"
            },
            {
                "cds_end_max": 134411853,
                "cds_start_min": 134402914,
                "gene_entrez_id": 91368,
                "gene_symbol": "CDKN2AIPNL",
                "reference_name": "5"
            }
        ]
    },
    "errors": [],
    "warnings": []
}
```
<!--/podmd-->
