# API: Beacon Services

The _bycon_ environment provides a number of data services beyond typical Beacon
functionality. These services can be loosely grouped into two major types:

* services which extend Beacon formats, _i.e._ use Beacon concepts and query
  parameters but provide non-standard output
    - plotting functions
    - tabular and text output
    - aggregated data such as CNV frequencies (see [_intervalFrequencies_](services/intervalFrequencies.md))
* services which make use of utility function and data existing primarily for the
  support of Beacon functionality
    - ontology term cross mapping
    - geneId to location lookup
    - geographic location mapping and map projections (see [_geolocations_](services/geolocations.md))
    - ISCN cytogenetic band mapping
    - publication data for cancer genome screening publications

!!! info "API Parameters"
    A complete list of parameters accepted by the API is provided on the [_Web and Command Line Parameters_](API-parameters.md) page.

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

#### Request Example

* <{{config.reference_server_url}}/services/genespans?geneId=CDKN2>

## Plotting

The `byconServices` package inside `bycon` provides a number of plotting functions which can be used to visualize the data in the database. Generally
plot functionality is focussed on generating CNV visualizations for per-sample and
aggregated CNV data (e.g. frequencyplots). Additionally some geographic map projectins are provided e.g. for samples and metadata.

More information can be found in the plot documentation on [this page](plotting.md).

## List of Services

{%
    include-markdown "generated/beacon-services.md"
%}

