# Beacon Responses

The following is a list of standard Beacon responses supported by the `bycon` package.
Responses for individual entities or endpoints are grouped by their Beacon framework
response classes (e.g. `beaconResultsetsResponse` for `biosamples`, `g_variants` etc.).



Please be reminded about the general syntax used in Beacon: A **path element** such
as `/biosamples` corresponds to an entity (here `biosample`). Below these relations
are indicated by the `@` symbol.



#### Schemas **{S}**, Tests **{T}** and Examples **{E}**
Tests, examples and schemas are run from the server defined in this site's build instructions
(see the `reference_server_url` entry in `mkdocs.yaml` file in the repository's root).


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



## beaconResultsetsResponse

A `beaconResultsetsResponse` returns the results of a query against a beacon, which - beyond the summary count response for overall matches - contains details about the matches in individual **collections** in the beacon or beacon network. The types of `beaconResultsets` objects are defined in the beacon's configuration; if using the Beacon v2+ default model the types `dataset` and `cohort` are supported. `beaconResultsets` typically contain a list of records matched by the query.

* **{S}** <{{config.reference_server_url}}/services/schemas/beaconResultsetsResponse>

### genomicVariant @ `/g_variants`

* **{S}** <{{config.reference_server_url}}/services/schemas/genomicVariant>

* **{T}** <{{config.reference_server_url}}/beacon/g_variants?testMode=true>

* **{E}** <{{config.reference_server_url}}/beacon/g_variants/pgxvar-5bab576a727983b2e00b8d32>

* **{E}** <{{config.reference_server_url}}/beacon/g_variants/pgxvar-5bab576a727983b2e00b8d32/individuals>

* **{E}** <{{config.reference_server_url}}/beacon/g_variants?geneId=CDKN2A&variantMaxSize=100000&limit=5>

* **{E}** <{{config.reference_server_url}}/beacon/g_variants?referenceName=NC_000017.11&start=7577120&referenceBases=G&alternateBases=A>



### analysis @ `/analyses`

The `analysis` schema represents a information about the data analysis steps leading to (a set of) genomic variation call(s).



* **{S}** <{{config.reference_server_url}}/services/schemas/analysis>

* **{T}** <{{config.reference_server_url}}/beacon/analyses?testMode=true>



### run @ `/runs`

Schema for the experimental run (e.g. sequencing run, array processing...) leading to the raw data for the (computational) analysis. NOTE: In the bycon environment run parameters are stored in the analysis documents and rewritten into this schema at export time.



* **{S}** <{{config.reference_server_url}}/services/schemas/run>

* **{T}** <{{config.reference_server_url}}/beacon/runs?testMode=true>



### biosample @ `/biosamples`

A Biosample refers to a unit of biological material from which the substrate molecules (e.g. genomic DNA, RNA, proteins) for molecular analyses (e.g. sequencing, array hybridisation, mass-spectrometry) are extracted. Examples would be a tissue biopsy, a single cell from a culture for single cell genome sequencing or a protein fraction from a gradient centrifugation. Several instances (e.g. technical replicates) or types of experiments (e.g. genomic array as well as RNA-seq experiments) may refer to the same Biosample.



* **{S}** <{{config.reference_server_url}}/services/schemas/biosample>

* **{T}** <{{config.reference_server_url}}/beacon/biosamples?testMode=true>

* **{E}** <{{config.reference_server_url}}/beacon/biosamples?filters=NCIT:C4017&limit=3>

* **{E}** <{{config.reference_server_url}}/beacon/biosamples?referenceName=refseq:NC_000009.12&variantType=EFO:0030067&start=21000000,21975098&end=21967753,23000000&filters=NCIT:C3058&limit=10>



### individual @ `/individuals`

None



* **{S}** <{{config.reference_server_url}}/services/schemas/individual>

* **{T}** <{{config.reference_server_url}}/beacon/individuals?testMode=true>

* **{E}** <{{config.reference_server_url}}/beacon/individuals?filters=EFO:0030049&limit=5>



## beaconFilteringTermsResponse

The filtering terms response provides information about available individual filters for a beacon's entry types as well as optional information about the ontologies the filters belong to.

* **{S}** <{{config.reference_server_url}}/services/schemas/beaconFilteringTermsResponse>

### filteringTerm @ `/filtering_terms`

Schema for the Filtering Terms list related to the hosting entry type. It is kept separated to allow updating it independently.



* **{S}** <{{config.reference_server_url}}/services/schemas/filteringTermsSchema>

* **{T}** <{{config.reference_server_url}}/beacon/filtering_terms?testMode=true>



## beaconInfoResponse

Information about the Beacon. Aimed at Beacon clients like web pages or Beacon networks.

* **{S}** <{{config.reference_server_url}}/services/schemas/beaconInfoResponse>

### info @ `/info`

Metadata describing a Beacon instance.

The `info` endpoint provides information about the Beacon, such as its name, the organization responsible for the Beacon, a contact email, and the API version. It is based on the GA4GH `service-info` standard.



* **{S}** <{{config.reference_server_url}}/services/schemas/beaconInfoResults>

* **{T}** <{{config.reference_server_url}}/beacon/info>



## beaconMapResponse

Information about the Beacon. Aimed to Beacon clients like web pages or Beacon networks.

* **{S}** <{{config.reference_server_url}}/services/schemas/beaconMapResponse>

### beaconMap @ `/map`

Map of a Beacon, its entry types and endpoints. It isconceptually similar to a website sitemap.

The `beaconMap` object provides a map of the Beacon's REST endpoints.



* **{S}** <{{config.reference_server_url}}/services/schemas/beaconMapSchema>

* **{T}** <{{config.reference_server_url}}/beacon/map>



## beaconConfigurationResponse

Information about the Beacon. Aimed to Beacon clients like web pages or Beacon networks.

* **{S}** <{{config.reference_server_url}}/services/schemas/beaconConfigurationResponse>

### configuration @ `/configuration`

Files complaint with this schema are the configuration ones. The details returned in `service-info` are mirroring the ones in this configuration file.



* **{S}** <{{config.reference_server_url}}/services/schemas/beaconConfigurationSchema>

* **{T}** <{{config.reference_server_url}}/beacon/configuration>



## beaconEntryTypesResponse

Response including a list of Entry types definitions.

* **{S}** <{{config.reference_server_url}}/services/schemas/beaconEntryTypesResponse>

### entryType @ `/entry_types`

Schema for the entry types list.



* **{S}** <{{config.reference_server_url}}/services/schemas/entryTypesSchema>

* **{T}** <{{config.reference_server_url}}/beacon/entry_types>



