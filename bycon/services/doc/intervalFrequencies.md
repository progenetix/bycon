<!--podmd-->
## _intervalFrequencies_

This service provides access to binned CNV frequency information of data
"collations" in the Progenetix project databases. A typical use would be the
retrieval of data for a single collation, e.g. by its identifier (e.g.
`NCIT:C7376`, `PMID:22824167`, `pgxcohort-TCGAcancers`).

#### Response

Results are provides in a JSON Beacon v2 response, inside the `results`
array. Each frequency set is provided as object, with the single bin frequencies
in `interval_frequencies`.

For the usual "single frequency set" use case this would result in a possible
direct access to the frequecy list at `results[0].interval_frequencies`.

```
{
  "meta": {
    ...
  },
  "response": {
    "error": {
      "errorCode": 200,
      "errorMessage": ""
    },
    "exists": true,
    "numTotalResults": 1,
    "results": [
      {
        "datasetId": "progenetix",
        "id": "pgxcohort-TCGAcancers",
        "intervalFrequencies": [
          {
            "referenceName": "1",
            "end": 1000000,
            "gainFrequency": 0,
            "no": 1,
            "loss_frequency": 0,
            "start": 0
          },
          {
            "referenceName": "1",
            "end": 2000000,
            "gainFrequency": 0,
            "no": 2,
            "lossFrequency": 0,
            "start": 1000000
          },
```

#### Parameters

##### `id`

* standard parameter to retrieve a frequency set by its `id`
* available values can be looked up using the [`collations`](collations.md)
service:
  - <https://progenetix.org/services/collations?method=ids&filters=NCIT&datasetIds=progenetix>
* an `id` value will override any given `filters`

##### `filters`

* a single or a comma-concatenated list of identifiers

##### `intervalType`

* not implemented
* default use is 1Mb, i.e. megabase binning (with diverging size for each
chromosome's q-terminal interval)

##### `output`

The output parameter here can set set autput format. Options are:

* not set ...
  - standard JSON response
* `output=pgxseg`
  - Proggenetix `.pgxseg` columnar format, with a line for each interval and gain, loss frequencies
* `output=pgxmatrix`
  - Progenetix `.pgxmatrix` matrix format, with a line for each frequency set and interval frequencies provided in the columns (i.e. usually first all gain frequencies, then all loss frequencies)
  - makes sense for multiple frequency sets, e.g. for clustering

#### Examples

* <https://progenetix.org/services/intervalFrequencies/?id=pgxcohort-TCGAcancers>
* <https://progenetix.org/services/intervalFrequencies/?filters=NCIT:C7376,PMID:22824167>
* <https://progenetix.org/services/intervalFrequencies/?output=pgxseg&filters=NCIT:C7376,PMID:22824167>
* <https://progenetix.org/services/intervalFrequencies/?output=pgxmatrix&filters=NCIT:C7376,PMID:22824167>

<!--/podmd-->
