# Beacon Responses

The following is a list of standard Beacon responses supported by the `bycon` package.
Responses for individual entities or endpoints are grouped by their Beacon framework
response classes (e.g. `beaconResultsetsResponse` for `biosamples`, `g_variants` etc.).

Please be reminded about the general syntax used in Beacon: A **path element** such
as `/biosamples` corresponds to an entity (here `biosample`). Below these relations
are indicated by the `@` symbol.


## beaconInfoResponse

### info @ `/info`

#### Description

The `info` endpoint provides information about the Beacon, such as its name, the organization responsible for the Beacon, a contact email, and the API version. It is based on the GA4GH `service-info` standard.

#### Schema for _configuration_

* <https://progenetix.org/services/schemas/beaconInfoResults/>

#### Tests

* <{{config.reference_server_url}}/beacon/info>



## beaconMapResponse

### beaconMap @ `/map`

#### Description

The `beaconMap` object provides a map of the Beacon's REST endpoints.

#### Schema for _map_

* <https://progenetix.org/services/schemas/beaconMapSchema/>

#### Tests

* <{{config.reference_server_url}}/beacon/map>



## beaconConfigurationResponse

### configuration @ `/configuration`

#### Schema for _configuration_

* <https://progenetix.org/services/schemas/beaconConfigurationSchema/>

#### Tests

* <{{config.reference_server_url}}/beacon/configuration>



## beaconEntryTypesResponse

### entryType @ `/entry_types`

#### Schema for _entryType_

* <https://progenetix.org/services/schemas/entryTypesSchema/>

#### Tests

* <{{config.reference_server_url}}/beacon/entry_types>



## beaconFilteringTermsResponse

### filteringTerm @ `/filtering_terms`

#### Schema for _filteringTerm_

* <https://progenetix.org/services/schemas/filteringTermsSchema/>

#### Tests

* <{{config.reference_server_url}}/beacon/filtering_terms?testMode=true>



## beaconResultsetsResponse

### analysis @ `/analyses`

#### Schema for _analysis_

* <https://progenetix.org/services/schemas/analysis/>

#### Tests

* <{{config.reference_server_url}}/beacon/analyses?testMode=true>



### biosample @ `/biosamples`

#### Schema for _biosample_

* <https://progenetix.org/services/schemas/biosample/>

#### Tests

* <{{config.reference_server_url}}/beacon/biosamples?testMode=true>

* <{{config.reference_server_url}}/beacon/biosamples?filters=NCIT:C4017&limit=3>



### genomicVariant @ `/g_variants`

#### Schema for _genomicVariant_

* <https://progenetix.org/services/schemas/genomicVariant/>

#### Tests

* <{{config.reference_server_url}}/beacon/g_variants?testMode=true>

* <{{config.reference_server_url}}/beacon/g_variants?geneId=CDKN2A&variantMaxSize=100000&limit=5>



### individual @ `/individuals`

#### Schema for _individual_

* <https://progenetix.org/services/schemas/individual/>

#### Tests

* <{{config.reference_server_url}}/beacon/individuals?testMode=true>

* <{{config.reference_server_url}}/beacon/individuals?filters=EFO:0030049&limit=5>



### run @ `/runs`

#### Schema for _run_

* <https://progenetix.org/services/schemas/run/>

#### Tests

* <{{config.reference_server_url}}/beacon/runs?testMode=true>



## beaconCollectionsResponse

### cohort @ `/cohorts`

#### Schema for _cohort_

* <https://progenetix.org/services/schemas/cohort/>

#### Tests

* <{{config.reference_server_url}}/beacon/cohorts?testMode=true>



### dataset @ `/datasets`

#### Schema for _dataset_

* <https://progenetix.org/services/schemas/dataset/>

#### Tests

* <{{config.reference_server_url}}/beacon/datasets?testMode=true>



