<!--podmd-->
## Bycon _services_

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

### `services.py` and URL Mapping

The service URL format `progenetix.org/services/__service-name__?parameter=value`
is a shorthand for `progenetix.org/cgi-bin/bycon/services/__service-name__.py?parameter=value`.

The `services` application deparses a request URI and calls the respective
script. The functionality is combined with the correct configuration of a 
rewrite in the server configuration:

```
RewriteRule     "^/services(.*)"     /cgi-bin/bycon/services/services.py$1      [PT]
```

### Response formats

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

##### Request  Example

* <https://progenetix.org/services/genespans?geneId=CDKN2>

##### Response Example

```
{
    "meta": {
      "info": "The main geolocs payload can be accessed in `response.results`.\n",
      "received_request": {
        "assemblyId": "GRCh38",
        "geneId": "TP53"
      },
      "response_entity_id": "genespans",
      "returned_schemas": {
        "GeneSpan": "https://progenetix.org/services/schemas/GeneSpan/"
      },
    },
    "response": {
        "error": {},
        "exists": true,
        "info": {
          "count": 17
        },
        "results": [
            {
                "end": 21994330,
                "start": 21968228,
                "gene_entrez_id": 1029,
                "gene_symbol": "CDKN2A",
                "reference_name": "9"
            },
            {
                "end": 183447426,
                "start": 183444797,
                "gene_entrez_id": 55602,
                "gene_symbol": "CDKN2AIP",
                "reference_name": "4"
            },
            {
                "end": 134411853,
                "start": 134402914,
                "gene_entrez_id": 91368,
                "gene_symbol": "CDKN2AIPNL",
                "reference_name": "5"
            }
        ]
    }
}
```
<!--/podmd-->
