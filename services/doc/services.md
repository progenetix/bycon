<!--podmd-->
## Bycon _services_

The _bycon_ environment provides a number of data services which make use of
resources in the _Progenetix_ environment. Please refer to their specific
documentation.

* [_biosamples_](biosamples.md)
* [_collations_](collations.md)
* [_cytomapper_](cytomapper.md)
* [_deliveries_](deliveries.md)
* [_genespans_](genespans.md)
* [_geolocations_](geolocations.md)
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

* <https://progenetix.org/services/genespans?geneSymbol=CDKN2>

##### Response Example

```
{
    "meta": {
      "info": "The main geolocs payload can be accessed in `response.results`.\n",
      "parameters": {
        "assemblyId": "GRCh38",
        "geneSymbol": "TP53"
      },
      "response_type": "genespans",
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
