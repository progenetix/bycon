## beaconCollectionsResponse

A type of Beacon response that includes details about the **collections** in a beacon. The types of collections are defined in each beacon's configuration; if using the Beacon v2+ default model usually the types `dataset` and `cohort` are supported.

* **{S}** <{{config.reference_server_url}}/services/schemas/beaconCollectionsResponse>

### dataset @ `/datasets`

A dataset available in the beacon.



* **{S}** <{{config.reference_server_url}}/services/schemas/dataset>

* **{T}** <{{config.reference_server_url}}/beacon/datasets?testMode=true>

* **{E}** <{{config.reference_server_url}}/beacon/datasets/progenetix>



### cohort @ `/cohorts`

A cohort available in the beacon.



* **{S}** <{{config.reference_server_url}}/services/schemas/cohort>

* **{T}** <{{config.reference_server_url}}/beacon/cohorts?testMode=true>





## beaconInfoResponse

The `beaconInfoResponse` provides metadata describing a Beacon instance, such as its name, the organization responsible for the Beacon, contact information, site logo and alternative URLs and importantly the beacon's API version. It is based on the GA4GH `service-info` standard.
The content of the `beaconInfoResponse` can be used by clients such as web front ends or beacon aggregators to evaluate potential access patterns and to display information about the beacon.

* **{S}** <{{config.reference_server_url}}/services/schemas/beaconInfoResponse>

### info @ `/info`

Metadata describing a Beacon instance.



* **{S}** <{{config.reference_server_url}}/services/schemas/beaconInfoResults>

* **{T}** <{{config.reference_server_url}}/beacon/info>





## beaconConfigurationResponse

The `beaconConfigurationResponse` returns information about configuration parameters of a given beacon instance such as maturity or security attributes or supported entry types. It is directed towards Beacon clients like web pages or network aggregators.

* **{S}** <{{config.reference_server_url}}/services/schemas/beaconConfigurationResponse>

### configuration @ `/configuration`

The Beacon configuration reports several attributes of the beacon instance related to security, maturity and available entry types. Where appropriate the details returned in `service-info` should mirror the ones in this configuration.



* **{S}** <{{config.reference_server_url}}/services/schemas/beaconConfigurationSchema>

* **{T}** <{{config.reference_server_url}}/beacon/configuration>





## beaconBooleanResponse

Complete definition for a minimal response that provides *only* an aggregate Boolean `"exists": true` or `"exists": false` answer to the query.  
Additional information - which should not consist of record-level information - can be provided through `beaconHandovers`.  

* **{S}** <{{config.reference_server_url}}/services/schemas/beaconBooleanResponse>


For a list of entities potentially served by `beaconBooleanResponse` depending on
the selected or granted `responseGranularity` please check `beaconResultsetsResponse`.


## beaconFilteringTermsResponse

The filtering terms response provides information about available individual filters for a beacon's entry types as well as optional information about the ontologies the filters belong to.

* **{S}** <{{config.reference_server_url}}/services/schemas/beaconFilteringTermsResponse>

### filteringTerm @ `/filtering_terms`

Schema for the Filtering Terms list related to the hosting entry type. It is kept separated to allow updating it independently.



* **{S}** <{{config.reference_server_url}}/services/schemas/filteringTermsSchema>

* **{T}** <{{config.reference_server_url}}/beacon/filtering_terms?testMode=true>





## beaconErrorResponse

A `beaconErrorResponse` denotes an unsuccessful operation, e.g. due to a missing parameter or an invalid query. The response contains an error object.

* **{S}** <{{config.reference_server_url}}/services/schemas/beaconErrorResponse>



## beaconMapResponse

A `beaconMapResponse` provides information about the beacon instance such as the different endpoints supported by this implementation of the Beacon API. This response is aimed to allow Beacon clients such as web front ends and Beacon network aggregators to evaluate which access patterns can be implemented against individual beacons.

* **{S}** <{{config.reference_server_url}}/services/schemas/beaconMapResponse>

### beaconMap @ `/map`

Map of a Beacon, its entry types and endpoints. It isconceptually similar to a website sitemap.



* **{S}** <{{config.reference_server_url}}/services/schemas/beaconMapSchema>

* **{T}** <{{config.reference_server_url}}/beacon/map>





## beaconResultsetsResponse

A `beaconResultsetsResponse` returns the results of a query against a beacon or beacon aggregator. Beyond the `responseSummary` for overall matches the response contains details about the matches in individual **collections** in the beacon or beacon network. This type of response is required when serving a request with a "record" level `responseGranularity`, and `beaconResultsets` typically contain a list of records matched by the query.
The types of `beaconResultsets` objects are defined in the beacon's configuration; e.g. if using the Beacon v2+ default model the types `dataset` and `cohort` are supported as result sets.    

* **{S}** <{{config.reference_server_url}}/services/schemas/beaconResultsetsResponse>

### genomicVariant @ `/g_variants`

The type of response used for the endpoint depends on the requested and granted `responseGranularity`.



* **{S}** <{{config.reference_server_url}}/services/schemas/genomicVariant>

* **{T}** <{{config.reference_server_url}}/beacon/g_variants?testMode=true>

* **{E}** <{{config.reference_server_url}}/beacon/g_variants/pgxvar-5bab576a727983b2e00b8d32>

* **{E}** <{{config.reference_server_url}}/beacon/g_variants/pgxvar-5bab576a727983b2e00b8d32/individuals>

* **{E}** <{{config.reference_server_url}}/beacon/g_variants?geneId=CDKN2A&variantMaxSize=100000&limit=5>

* **{E}** <{{config.reference_server_url}}/beacon/g_variants?referenceName=NC_000017.11&start=7577120&referenceBases=G&alternateBases=A>



### analysis @ `/analyses`

The `analysis` schema represents a information about the data analysis steps leading to (a set of) genomic variation call(s).

The type of response used for the endpoint depends on the requested and granted `responseGranularity`.



* **{S}** <{{config.reference_server_url}}/services/schemas/analysis>

* **{T}** <{{config.reference_server_url}}/beacon/analyses?testMode=true>



### run @ `/runs`

Schema for the experimental run (e.g. sequencing run, array processing...) leading to the raw data for the (computational) analysis. NOTE: In the bycon environment run parameters are stored in the analysis documents and rewritten into this schema at export time.

The type of response used for the endpoint depends on the requested and granted `responseGranularity`.



* **{S}** <{{config.reference_server_url}}/services/schemas/run>

* **{T}** <{{config.reference_server_url}}/beacon/runs?testMode=true>



### biosample @ `/biosamples`

A Biosample refers to a unit of biological material from which the substrate molecules (e.g. genomic DNA, RNA, proteins) for molecular analyses (e.g. sequencing, array hybridisation, mass-spectrometry) are extracted. Examples would be a tissue biopsy, a single cell from a culture for single cell genome sequencing or a protein fraction from a gradient centrifugation. Several instances (e.g. technical replicates) or types of experiments (e.g. genomic array as well as RNA-seq experiments) may refer to the same Biosample.

The type of response used for the endpoint depends on the requested and granted `responseGranularity`.



* **{S}** <{{config.reference_server_url}}/services/schemas/biosample>

* **{T}** <{{config.reference_server_url}}/beacon/biosamples?testMode=true>

* **{E}** <{{config.reference_server_url}}/beacon/biosamples?filters=NCIT:C4017&limit=3>

* **{E}** <{{config.reference_server_url}}/beacon/biosamples?referenceName=refseq:NC_000009.12&variantType=EFO:0030067&start=21000000,21975098&end=21967753,23000000&filters=NCIT:C3058&limit=10>



### individual @ `/individuals`

None

The type of response used for the endpoint depends on the requested and granted `responseGranularity`.



* **{S}** <{{config.reference_server_url}}/services/schemas/individual>

* **{T}** <{{config.reference_server_url}}/beacon/individuals?testMode=true>

* **{E}** <{{config.reference_server_url}}/beacon/individuals?filters=EFO:0030049&limit=5>



### phenopacket @ `/phenopackets`

The Phenopacket class is a bare-bones JSON-schema rewrite of the Phenopackets v2 standard.

The type of response used for the endpoint depends on the requested and granted `responseGranularity`.
In the `bycon` framework Phenopackets are generated at export time by aggregating the relevant information from the matched `individual`, `biosample`s, `analysis`(/es) and `genomicVariation`s.



* **{S}** <{{config.reference_server_url}}/services/schemas/phenopacket>

* **{T}** <{{config.reference_server_url}}/beacon/phenopackets?testMode=true>

* **{E}** <{{config.reference_server_url}}/beacon/phenopackets?filters=EFO:0030049&limit=5>





## beaconEntryTypesResponse

The `beaconEntryTypesResponse` provides information about the entry types served through a beacon, including their definitions and pointers to their schemas.

* **{S}** <{{config.reference_server_url}}/services/schemas/beaconEntryTypesResponse>

### entryType @ `/entry_types`

Schema for the entry types list.



* **{S}** <{{config.reference_server_url}}/services/schemas/entryTypesSchema>

* **{T}** <{{config.reference_server_url}}/beacon/entry_types>





## beaconCountResponse

Complete definition for a minimal response that provides an aggregate Boolean `"exists": true` or `"exists": false` answer to the query as well as the count of the matched records.
Additional information - which should not consist of record-level information - can be provided through `beaconHandovers`.  

* **{S}** <{{config.reference_server_url}}/services/schemas/beaconCountResponse>


For a list of entities potentially served by `beaconBooleanResponse` depending on
the selected or granted `responseGranularity` please check `beaconResultsetsResponse`.


