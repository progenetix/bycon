<!--podmd-->
## _intervalFrequencies_

This service provides access to binned CNV frequency information of data
"collations" in the Progenetix project databases. A typical use would be the
retrieval of data for a single collation, e.g. by its identifier (e.g.
`NCIT:C7376`, `PMID:22824167`, `pgxcohort-TCGAcancers`).

#### Response

Results are provides in a JSON Beacon v2 response, inside the `response.results`
array. Each frequency set is provided as object, with the single bin frequencies
in `interval_frequencies`.

For the usual "single frequency set" use case this would result in a possible
direct access to the frequecy list at `response.results[0].interval_frequencies`.

```
{
  "meta": {
    ...
  },
  "response": {
    "error": {
      "error_code": 200,
      "error_message": ""
    },
    "exists": true,
    "numTotalResults": 1,
    "results": [
      {
        "dataset_id": "progenetix",
        "id": "pgxcohort-TCGAcancers",
        "interval_frequencies": [
          {
            "chro": "1",
            "end": 1000000,
            "gain_frequency": 0,
            "index": 0,
            "loss_frequency": 0,
            "start": 0
          },
          {
            "chro": "1",
            "end": 2000000,
            "gain_frequency": 0,
            "index": 1,
            "loss_frequency": 0,
            "start": 1000000
          },
```

#### Parameters

##### `id`

* standard parameter to retrieve a frequency set by its `id`
* available values can be looked up using the [`collationc`](collations.md)
service:
  - <https://progenetix.org/services/collations?method=ids&filters=NCIT&datasetIds=progenetix>
* an `id` value will override any given `filters`

##### `filters`

* a single or a comma-concatenated list of identifiers

##### `intervalType`

* not implemented
* default use is 1Mb, i.e. megabase binning (with diverging size for each
chromosome's q-terminal interval)

#### Examples

* <https://progenetix.org/services/intervalFrequencies/?datasetIds=progenetix&id=pgxcohort-TCGAcancers>
* <https://progenetix.org/services/intervalFrequencies/?datasetIds=progenetix&filters=NCIT:C7376,PMID:22824167>

<!--/podmd-->
