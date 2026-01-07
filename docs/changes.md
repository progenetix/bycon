# Changes & To Do

## Changes Tracker

While changes are documented for individual point versions we actually do not
push releases out for all of them; they serve more as internal development
milestones.

### 2026-01-10 (v2.7.1)

* further refactoring of summaries processing
    - `bycon` - renaming of `aggregator_definitions` to `summaries_definitions` to keep a distinction from Beacon aggregation (_i.e._ involving multiple beacons)
    - `beaconplusWeb` with several changes in `components/summaries`, generally
      involving code "reshaping" but no major functional changes

### 2025-12-31 (v2.7.0 "That Was 2025")

* `beaconplusWeb` front end updates
    - refactored data summaries source in `src/components/summaries/`
    - improving of documentation in <https://bycon.progenetix.org/data-summaries/>

### 2025-12-22 (v2.7.0+pre1)

* de-nested the `classificationTrees` into single tupe specific files
  and moved the additional sources for their generation outside of the project
    - also renamed some files/filter types (e.g. `NCIT` ==> `NCITneoplasm`, `NCITsex` ==> `pgxSex`)
* in `beaconplusWeb` changes to `AggregationPlots`
    - moved from `Victory` to `Plotly`; this requires `npm install react-plotly.js plotly.js`
* new `___BEACON_ROOT___/beacon/aggregation_terms` endpoint to indicate concepts
  for available data summaries

### 2025-12-12 (v2.6.9)

The recent changes addressed several issues with the aggregation implementation

* now `ByconSummaries` class
    - dimension agnostic, i.e. supports 1D, 2D, ... nD aggregations through the
      same methods
    - TODO: So far cross-entity aggregations are supported through some workarounds;
      e.g. some information stored in `individual` (sex, age, followup...) is
      repeated in the biosamples' `individual_info` property to allow biosample
      aggregations on individual properties. A more generic solution would be
      desirable, e.g. utilizing MongoDB's `$lookup`.
* added (expanding ...) [doumentation page](/data-summaries/) about the Beacon Aggregation development

### 2025-11-28 (v2.6.8 "Aggregator")

* extending aggregation responses to support 2-dimensional aggregations
    - implemented in `ByconSummaries` class
    - now also supports `plot_type: "stackedBar"` for the dashboard

### 2025-11-18 (v2.6.7 "DashboardDabbler")

* implemented a basic dashboard at `___BEACON_ROOT___/dataDashboard/` using the
  draft version of a Beacon v2.n aggregation response
    - simple Victory based bar plots defined in `beaconplusWeb/src/components/AggregatedPlots.js`
    - only one-dimensional so far; 2-dimensional for stacked plots coming up
* ... based on the `ByconSummaries` class to handle aggregation definitions
      and processing
    - added `aggregation_definitions.yaml` file for defining available aggregations
      and their parameters
    - modified `ByconResultSets` to include aggregation processing if requested
      through the `aggregated` granularity parameter
* added a new `individual_info` object property to biosamples which contains 
  data extracted from the corresponding individual, to allow easier aggregation
    - one has to run the updated `housekeeping.py` script to populate this field
```
  individual_info: {
    index_disease: {
      disease_code: { id: 'NCIT:C8851', label: 'Diffuse Large B-Cell Lymphoma' },
      stage: { id: 'NCIT:C27966', label: 'Stage I' },
      clinical_tnm_finding: [ { id: 'NCIT:C48720', label: 'T1 Stage Finding' } ],
      followup_state: { id: 'EFO:0030049', label: 'dead (follow-up status)' },
      followup_time: 'P1M',
      onset: { age: 'P41Y', age_days: 14974 },
      followup_days: 30
    },
    sex: { id: 'NCIT:C16576', label: 'female' }
```


### 2025-11-04 (v2.6.6 "GlobeProjector")

* created ByconHO class in `beacon_responses.py` and deleted `handover_generation.py`
* created new `/services/sampleglobe` endpoint for plotting sample provenance
  on a globe projection using [Globe.gl](https://globe.gl)

### 2025-11-03 (v2.6.5 "geonames")

* updated the `geolocs` database with the latest GeoNames dump (2025-10-29)
    - now using `cities500`, _i.e._ 10x the number of previous entries
    - created `geoUpdater.py` housekeeping script for future updates of the
      `geolocs` collection
    - added a function to `housekeeping.py` to update the `geo_location` in
      biosamples from the existing long, lat data to pull the nearest match from
      the `geolocs` collection
        * side effect are now some rather granular annotations; e.g. New York
          coordinates which point to Manhattan are now labeled as "Financial District"
          instead of "New York City"
        * unknown coords ar now all mapped to Atlantis which - as everyone knows -
          is the sunken place below the Bermuda Triangle (centered at about lat: 25, long: -71)
    - ... above now handled by `ByconGeoResource` class

### 2025-10-23 (v2.6.4 `___BEACON_ROOT___`)

* 2025-10-24: v2.6.4.1 fixes pgxseg export
* changed from hard coded `https://progenetix.org` to template `___BEACON_ROOT___`
  in map, schema and configuration files and for handover generation
    - the `___BEACON_ROOT___` is replaced during request processing through the
      detected `f"{REQUEST_SCHEME}://{HTTP_HOST}"`
* fixed UCSC link generation for BeaconPlus
* removed `beaconMap.yaml` from `schemas`, since now part of `config/beacon_map.yaml`
* renamed `ENV` to `HTTP_HOST` for consistency
* new `dict_replace_values` function in `bycon_helpers.py`

### 2025-10-21 (v2.6.3 "Small Surgery"):

* schema file restructuring
    - removed all JSON schemas fromn the source tree since they are generated
      from YAML anyway and changed the file targets in `schema_parsing.py` to
      `.yaml` accordingly
    - flattened schema hierarchy structure since there is no need to distinguish
      between `src` and `json` directories anymore
    - removed the `schemas/bin` directory since no json files are generated anymore
    - adjusted documentation generation in `markdowner.py` accordingly
* cleaned out code w/ removal of "pgxVariant" references since using `vrsVariant`
    - e.g. in `ByconVariant` and `ByconBundler`

### 2025-10-13 (v2.6.2):

* refactored configuration files and processing to be more "Beacon standard":
    - moved the beacon_configuration.yaml to `config` and used as base for
      entry type configurations as well as for the `/configuration` endpoint
    - added database and collection parameters to `BYC_DBS` and removed the
      entry type specific ones from the entry type configurations
    - removed the `bycon_response_class` parameter and instead using now
      `BYC["info_responses"]` and `BYC["data_responses"]` to map main processing
    - retrieving the path for the entry types now from `/config/beacon_map.yaml`/`config/services_map.yaml`
      `rootUrl` and (custom) `rootUrlAliases`
    - modified configuration reading in `bycon/__init__.py` accordingly

### 2025-10-13: (v2.6.1):

* proper parsing of age and followup filters (`ageAtDiagnosis`, `followupTime`)
    - added the respective fields to the query form, additionally to the `freeFilters`
      test option from 2.6.0
* some reconfiguration of configuration processing
    - add the config readers directly to `__init__.py`, removing `read_specs.py`
    - now `domain_definitions` directory in `bycon/local/` with single file per
      base domain; `localhost.yaml` serves for defaults
    - now `dataset_definitions` directory in `bycon/local/` with single file per
      dataset
    - added environmental variable `BYC_LOCAL_CONF` to enable free placement
      of the `local` directory outside of the project

### 2025-10-08: (v2.6.0)

* further work on VRSification
* some temporary fixes for the `vrs_translator.py` to allow
  processing of some generic Progenetix variants, in combination
  with (temporary) `vrsifier.py` housekeeping script etc.
* (re-)adding an option to query follow-up times, supported by a calculated 
  `index_disease.followup_days` field in the database
* adding a `freeFilters` text field to the front end (which 
  is especially useful for alphanumerics such as `followupTime:>P12M,followupTime:<=P13M`)


### 2025-08-22: (v2.6.0+pre-VRSv2-adoption)

**Breaking Change**

This is the first PR to introduce changes needed for representing Progenetix variants in VRSv2 format. It includes the use of a `vrs_translator.py`, derived from vrs-python and with added formats for pgxseg CNV import but also a rudimentary class for `Adjacency` (limited to the structural variant needs of `bycon`/Progenetix).

Supported variant types so far are

* Allele (using the standard vrs-python code) with added `pgxseg` input format)
* Adjacency (implemented as new class w/ support for specific pgxadjoined input string)
* CopyNumberChange (again pgxseg input and some trimming of the vrs-python methods)

The changes include some redefinition of the variant input table format.

The  use of the current version requires some reprocessing of existing variants using the `vrsifier.py` temporary housekeeping script, as well as additional preparation (making sure all variants have a correct VRS "type") and clean-up.

**This PR is for internal distribution among the baudisgroup sites, not a release.**

#### Additional changes

* `ByconPlot` now splits `Adjacency` variants into 2 separate locations
  before plotting; so the 2 breakpoint/fusion regions are shown on
  their chromosomes (but no connections..., yet)
* fixing UCSC link for `.bed` display (they want `www.genome.ucsc.edu`, broken w/o "www")
* adding order check for start, end in bed file generation

### 2025-07-29: (v2.5.0 "Forked")

The 2.5.0 release does not contain additional functional changes compared to the
2.4.n but rather focusses on installation clean-up and code streamlining & maintenance:

#### Setup & procedural

* finally moving development process from "local cloud drive edits and random
  pushes to Github" to a more standard model w/ forks & PRs
* rewrite of the `setuptools` configuration, now using the recommended `pyproject.toml`
  format, and making some sense of the packaging structure during the process

#### Code & definitions

* more cleanup of temporary definitions etc.
* starting to move helpers into a class `ByconH`, e.g. `ByconH().truth(BYC_PARS.get("test_mode"))`
* refactoring `bycon_importer.py` and importers 
* adds a RecordsHierarchy class to `schema_parsing.py` for definition of the queried entities and their hierarchy
    - this also provides downstream and upstream functions
    - utilizes the RecordsHierarchy ... downstream etc. to slim down the importers and updaters etc.
* preparing for VRS 2 use by adding `ga4gh:SQ...` identifier aliases and adding a `ga4ghSQs()` and `ga4ghSQ(...)` functions to `ChroNames()`:
```
chr3:
  chr: "3"
  genbank_id: "CM000665.2"
  refseq_id: "refseq:NC_000003.12"
  sequence_id: "ga4gh:SQ.Zu7h9AggXxhTaGVsy7h_EZSChSZGcmgX"
```

### 2025-07-13: (v2.4.9 "Montréal")

* prototype for `summary_response`, currently limited to the to 
    - `__dataset_response_add_aggregations` as wrapper inside the `ByconResultSets`
      class
    - prototyping `__set_available_aggregation_ids` for adding filtering terms
      but so far no query aggregation implemented - this should be done through
        * taking the response entity
        * extracting the `target_values` from the corresponding `datasets_results[___dataset_id__][___coll___.id]`
        * combining a query from filter and id values
* some updates to internal schemas
    - aligning w/ recent Beacon model changes
    - adding the prototype for summary data
    - flattening schema structure, away from the `/___entity_path___/defaultSchema.yaml`
      to `/___entity___.yaml`

### 2025-06-13: (v2.4.8 "Friday the 13th")

* fixed `geoprov_id` based geolocation importing in `datatable_utils.py` and
  adjusted the publication table accordingly
* fixed recently broken importers (empty defaults post value assignments...)
* removed `geoloc_definitions`
    - new `GeoQuery()` class
    - parameters are now only defined in `argument_definitions` and limited to
      `["city","country","iso3166alpha2","iso3166alpha3","geo_latitude","geo_longitude","geo_distance"]` in the class itself (ATM)
* reversal of some of the `cnv_required_filters` ... option introduced in 2.4.6
    - this led to a problem at >220000 analyses, where then the query first
      matched all CNV samples before intersecting w/ the specific codes & therefore
      running into the upper limit of MongoDB
    - `EDAM:operation_3961` is now a hard filter in the `intervalAidFrequencyMaps`
      function (TODO: better solution?)

### 2025-06-05: (v2.4.7 "Thessaloniki")

* added a global `NO_PARAM_VALUES` which is used to set matching parameters (e.g. "none", "null", "undefined") to empty strings during input processing (circumvents issues with empty parameters in web front-ends)
* added clustering, tree generation and labels to the `histocircleplot` plot option
* started to move request tests to [Bruno](https://docs.usebruno.com/) (in `tests/bycon-tests`)
* circle plots are now clustered if more than one, with cluster tree and labels

### 2025-05-26: (v2.4.6)

* filter definitions in `filter_definitions.yaml` have now optional lists of
  filters to be in- or excluded when generating CNV frequency maps
    - this is helpful in cases like TCGA cohorts which include cancer and reference samples and e.g. one might want the cancer samples only
    - this works _only_ at the level of frequency map generation right now; for normal sample retrieval one just adds the parameterdirectly to the query
    - example:
```
    cnv_required_filters:
      - EFO:0009656
```

### 2025-05-19: (v2.4.5)

* more additions to the `beaconplusWeb` front end
    - plot parameters for the `/subsetsSearch/` endpoint
* plot parameter adjustments
    - change of the custom, concatenated `plotPars` format to support parameter
      concatenation by semicolon `;` (from `::`) and assignment to `:` (from `=`); e.g. `plotPars=plot_axis_y_max:75;plot_area_color=%23ccffdd;plot_gene_symbols:ESR1;plot_gene_symbols:MYC;plot_gene_symbols:TP53`
    - now support of multiple assignments - see `plot_gene_symbols` above
 

### 2025-05-19: (v2.4.4)

* extensive internal website code changes ("beaconplusWeb")
    - addes a new `/subsetsSearch/` endpoint to allow for multi-selection of
      subsets, e.g. to compare CNV histograms of different cancer types or from
      different internal databases (canver cell lines vs. overall Progenetix collection etc.)
    - added the multi-subset selection to the code trees (e.g. multi-checkmark
      selection of subsets for comparative CNV profile display)
    - some code re-organization to allow combination of project provided and
      additional (`/src/site-specific/`) parameter selections and examples
    - moved navifgation side column parameters and other website parameters
      to `/src/site-specific/layout.yaml`
* cohorts term fix

### 2025-05-15: (v2.4.3 "Bologna")

* expanded `pgxSex` ontology to have hierarchical terms with the current NCIT
  terms at the tip of the branches
    - e.g. `pgx:sex` => `pgx:sex-female` => `PATO:0020001` => `NCIT:C16576`
    - allows for query expansion & use of alternate terms (e.g. PATO)
    - not strictly correct since the NCIT terms are for "any description of biological
      sex or gender", wherease PATO is for genotypic sex; so might be flipped later
      w/ annotations in the databas switched accordingly (this was the orriginal
      state but Beacon docs used NCIT ...)
* changed `byconautServiceResponse` to `byconServiceResponse`
* added a new subset / cancer type histogram multi-selection to the
  `beaconplusWeb` front-end (at http://beaconplus.progenetix.org/subsetsSearch/)

### 2025-05-02 (v2.4.2)

* moving to the homebrew based server setup which includes a change of
  the local paths
    - also changes the name of the paths file from `local/local_pats.yaml` to `local/env_pats.yaml`

### 2025-04-25 (v2.4.1)

* fixing query aggregation where some upstream matches were incorrectly
  removed from the resultset
* some refactoring of parameter processing (esp. for `POST`) in a more modular way
    - also fixing some parameter parsing for `POST` where the "technical"
      parameters were expected to be outside of `query` (wrong) and then fixing the test examples accordingly

### 2025-04-25 (v2.4.0 "Cotswolds")

* transitioning from the deprecated `cgi` module for form parameter
  processing (`cgi.FieldStorage`) to `mycgi`
    - TODO: evaluate web framework or direct `urllib.parse` for form processing
* start with prototyping of `cohorts` files which should replace
  the auto-generation from `biosamples.cohorts.id` (though probably
  still keep using this parameter for the time being instead of being
  completely query defined)
* Bug fix: 
  - UCSC bed file did not include SNV variants due to wrong 
    `variantType` code (`EFO:0001059` instead of `SO:0001059` in `plot_variant_types`
    definition used for bed file subsetting)
  - UCSC link used 0-based start position => _i.e._ a single base change in the generated
    bed file was shown in a 2 base window (starting one too early)

### 2025-04-15 (v2.3.1)

* fixed a slowdown (existing for a long time...) in variant processing where
  the a new `ByconVariant` class was initiated for each processed variant
* added the option to have a variant response from a pure `filters` based
  request (e.g. `/biosamples?filters=NCIT:C3058`) although capping the variants
  returned at a limit of currently 300'000 (avoids time outs and running into
  MongoDB limits)
* added `NCITrace` filters class (`individual.ethnicity.id`)

### 2025-04-04 (v2.3.0 "Logan Airport")

* changed genespans response to have `chromosome` and `referenceName`
* fixed the geo query which had been broken by the query proocess refactoring
  in 2.2.3 (the new query uses a MongoDB aggregation which is not compatible
  with the geo `$near` query...)
* fix for some plot parameters where an incorrect auto-detection of sample strip
  height led to ignoring of modified values
* update to ICD-O topographu hierarchy where now the `C...9` "NOS" codes are
  treated as parent terms of the more specific ones

### 2025-03-10 (v2.2.6)

#### VQS & OpenAPI

* added several VQS parameter candidates to the `argument_definitions` file
    - these are by no means finalized; e.g. `breakpoint_range` and `adjacency_accession`
      are just placeholders for now
* added remapping of those parameters to existing parameters to keep the pre-defined
  queries for now => inside `__parse_variant_parameters`
      - e.g.
```Python
if "sequence_length" in v_p_k:
    if len(v_p) == 1:
        v_p.append(v_p[0] + 1)
    v_p_c.update({
        "variant_min_length": v_p[0],
        "variant_max_length": v_p[1]
    })
if "adjacency_accession" in v_p_k:
    v_p_c.update({"mate_name": self.ChroNames.refseq(v_p)})
```

### 2025-03-06 (v2.2.5)

* first partially functional version of the OpenAPI generation
    - not all services yet
    - main Beacon parameters but avoiding many optional parameters
    - served at `/api/` or `/services/api/`
    - rendered at the servers' root `.../api` (e.g. <https://progenetix.org/api>)

### 2025-03-03 (v2.2.4)

* created a new `PGXbed` class for handling of `.bed` file creation and UCSC link
generation.
    - `output=ucsc` creates the file & opens the UCSC link
    - `output=igv` creates an IGV bed file
    - without `output` parameter a UCSC-style bed file is created for download
* created a new `PGXvcf` class
* added the GeoJSON location to the `/beacon/service-info/` endpoint as proposed
  on [Github service-info](https://github.com/ga4gh-discovery/ga4gh-service-info/issues/73).
* plots: fixed bug where instead of the last chromosome band the second-to-last
  was plotted with a slimmer width/height ...
* preparation for a new `/api` endpoint
    - to provide OpenAPI mappings
    - currently residing in `/services` on the server which requires an addition
      to the server's rewrite rules (and restart etc. - YMMV)
        * `RewriteRule "^/?api/?$" ${BYCON_WEB_DIR}/services/api.py [PT]`
    - absolutely no practical functionality yet; purely for testing

### 2025-02-26 (v2.2.3)

* streamlining of internal data retrieval; now the storage objects for
  the matched ids are generated at the end of the rewritten query execution pipeline
* `PGXseg class`
    - for now only export handling
    - to be expanded fro file reading
    - needs template based parameter mapping & re-use of `__table_line_from_pgxdoc`
      method from `ByconDatatableExporter` etc.
    - additional fixes in the ByconBundler class for handling pgzseg imports
      (some of it will be refactored to PGXseg later on)
* `PGXfreq` class => used to export CNV frequency files (list or matrix)
* fixed gene position retrieval and `geneId` based queries
    - now able to handle multi-gene queries though additional constraints (size,
      CNV class) are the same for all genes
        * (beacon/biosamples/?geneId=CDKN2A,TP53&variantMinLength=10000&variantMaxLength=20000000&variantType=DEL&filters=NCIT:C3510)[http://progenetix.org/beacon/biosamples/?geneId=CDKN2A,TP53&variantMinLength=10000&variantMaxLength=20000000&variantType=DEL&filters=NCIT:C3510]


### 2025-02-21 (v2.2.2)

* fixed data retrieval for some services where the handover key wasn't defined
  for the specific service (e.g. samplemap) and the previous complex remapping
  had be removed

### 2025-02-21 (v2.2.1)

This is a test run for a major query module change:

* treating all queries individually in an AND context and aggregating by intyersection
  of id values
    - e.g. 2 filtering terms with value collision in the same property (e.g. `EFO:0010942,EFO:0010943`
      in `biosamples.biosample_status.id`) wwill run as separate internal db queries
      and the intersection of values will lead to an empty list for `biosample_id`
      but for a list of `individual_id` values for individuals which have both
      samples for EFO:0010942 ("primary tumor sample") and EFO:0010943 ("recurrent tumor sample")
    - this also applies to variant queries; _i.e._ the so far experimental mullti
      variant queries will result in matches for `analysis_id` values for such
      with both/multiple variants; or even only at a higher level if multiple
      samples ... (e.g. hit on germline and different on the tumor sample in same
      individual)
* TODO
    - extensive testing (check special queries especially => e.g. geo queries)
    - code cleanup
    - documentation
    - re-introduction of Boolean option ...


### 2025-02-14 (v2.2.0)

* fixed wrong aggregation of `individuals.sex` data (notes in the Progenetix news
  after updating ...)
* corrected filter logic where so far terms for the same field were treated as `OR`
  (which allows some nice multi-target queries but is in conflict w/ the Beacon behaviour)
* added `type` -> `VRStype` to variants => to be used for query disambiguation
    - currently `Adjacency` => `Allele` and `CopyNumberChange` are being used
    - query integration to follow
* modified the format for export of annotated variants (e.g. with `MolecularEffects`)
  to follow the Beacon schema (some nesting level mismatch before) 
* some code cleanup => e.g. adding some initialization functions which aren't used
  anywhere else to the root `__init__.py`.
* moved input parameter processing to new `ByconParameters` class
* fixed sample strip plots (some default nesting error)
* rewrite/finishing of Cytobands class and move to `genome_utils`
* schema parsing now in new `ByconSchemas` class

### 2025-02-08 (v2.1.5)

* fixed the all datasets info return for the `/datasets` endpoint

### 2025-01-29 (v2.1.4)

* some refactoring of file and table handling
* changed the URL generation for handovers to always use the protocol sequrity
  from the request (http or https)

### 2025-01-16 (v2.1.3)

* fixed publications query bug which was introduced by the recent
  `bycon` refactoring
* fixed `geoloc_utils.py` service library bug for empty marker sizes
* some removal of unused code
* `housekeepeing.py` now correctly asks for & uses global `--limit`

### 2024-12-20 (v2.1.2)

!!! warn "Python path"

    For various server configuration reasons the script shebang now references
    an absolute path to the Python interpreter at `#!/usr/local/bin/python3`. This
    might lead to the need to symlink the python binary from there; e.g. on a "Mn" Mac
    with a default homebrew installation through `ln -s /opt/homebrew/bin/python3 /usr/local/bin/python3`.

### 2024-12-19 (v2.1.1)

* Housekeepers updates:
    - rewrote `collationsFrequencymapsCreator.py` to avoid slow processing coming
      from use of standard query and bundle generation per collation
    - introduced `queriesTester.py` which can use generic parameters or a set of
      queries from `local/test_queries.yaml`
        * this is based on the new `MultiQueryResponses` class which can loop through
          multiple queries by injecting query parameters in BYC_PARS and then
          call `ByconResultSets()` and create a set of matched ids from all calls
    - modified `recordsSampler.py` to allow creation of example/excerpt datanases
      from query parameters or the `local/test_queries.yaml` definitions

### 2024-12-09 (v2.1.0)

* integration of the React based `BeaconPlus` front end into the project
* starting to provide integrated query examples which are then used also to
  pull (Progenetix) samples into the `examplez` dataset; therefore the query
  examples are guaranteed to provide responses in default builds

### 2024-11-22 (v2.0.13)

* introducing the option to set `DATABASE_NAMES` through an environmental
  parameter => to allow setups w/ external databases (thanks to Matt Baker!)
* wrapped the filter classes in the `filter_definitions` file into a
  `$defs` root parameter to allow for more structured definition of the filter parameters (e.g. `description` etc.)
* wrapped the argument definitions into a
  `$defs` root parameter
* added a `local/filter_definitions.yaml` file to allow local overrides of the
  filter definitions
* abandoned the `frequencymaps` collection in favour of the `frequencymap`s inside
  the `collations` collection
    - ¡¡¡ This requires re-generation of the maps !!!

### 2024-11-14 (v2.0.12)

* bug fix: the global HTTP_HOST was previously set to "local" if not called 
  over HTTP (`HTTP_HOST = environ.get('HTTP_HOST' => "local")`) which led
  to a wrong "local" context identification when testing from "localhost"; changed to `HTTP_HOST = environ.get('HTTP_HOST' => "___shell___")` and appropriate tests against this value

### 2024-11-14 (v2.0.11)

* properly have response code before document type in http header ...
* slight modification for parameter processing in `serices/genespans/`
* fixed missed splitting of `camelCase` list parameters => introduced
  some time last week...

### 2024-11-13 (v2.0.10)

* fixed some intermediary issue with a few service calls
* more explicit definition of `array` columns in import tables
* documentation now with generated and inlined information from
  some schemas into <https://bycon.progenetix.org/API/#api-beacon-responses>

### 2024-11-10 (v2.0.9)

Mostly work on schemas and generated documentation:

* removing examples etc. from the schemas since they're not tracked and don't represent anything bycon specific
* starting to improve top-level "description"s in schemas => which are then parsed using `markdowner.py`
* switching schema model internal references to own server instead of the hardcoded
  Github repo from the standard schema; e.g.
    - from <https://raw.githubusercontent.com/ga4gh-beacon/beacon-v2/main/framework/json/common/beaconCommonComponents.json#/definitions>
    - to <https://progenetix.org/services/schemas/beaconCommonComponents.json#/definitions>

### 2024-11-09 (v2.0.8)

* some library re-shuffling/condensation
* more work on circle plotting => e.g. separate class `ByconCircleTools`
* more documentation

### 2024-11-07 (v2.0.7)

* fixed `/datasets` response => recently broken during class refactoring
* added Beacon response documentation from parsing `entity_defaults` with the
  `markdowner.py` script into `/docs/generated`

### 2024-11-07 (v2.0.6)

* `histocircleplot`: [/services/collationplots/pgx:icdom-85003?plotType=histocircleplot&plotPars=plotTitle=Genomes+are+circular,+sometimes...](https://progenetix.org/services/collationplots/pgx:icdom-85003?plotType=histocircleplot&plotPars=plotTitle=Genomes+are+circular,+sometimes...)
    - this works for single collations
    - so far no gene label options etc.; just for fun...
* some further modification for the importer... scripts which are now reduced to very basic function callers

### 2024-10-28 (v2.0.5)

This update targets the example database:

* `housekeepers/recordsSampler.py` now provides a method to create an example database (currently hard coded to `examplez`)
based on a query towards a target database e.g. such as
```bash
./housekeepers/recordsSampler.py -d progenetix --filters "pgx:icdom-81703,pgx:icdom-94003" --filterLogic OR  --limit 222
```
* the project's `rsrc/mongodump/` directory contains now
    - the resulting `examplez` database dump (database contents might change over time)
    - a dump of the `_byconServicesDB` to be installed alongside for query support

The [documentation](https://bycon.progenetix.org/installation/#loading-and-maintaining-data) has been updated accordingly.

### 2024-10-22 (v2.0.4)

* fixed new `/ids` services bug
* fixed new `/publication` services bug
* modifications to table definitions
    - add `individuals.ethnicity`
    - added variants table generation for most frequent parameters

### 2024-10-21 (v2.0.3)

* bringing the documentation into `bycon`
    - seriously using Python heredocs => starting with embedding the main information
      about their functionality into the service caller functions
    - project root `markdowner.py` now parses services (and some preference
    files) into `.md` sources for website generation
        * see e.g. <http://bycon.progenetix.org/generated/services/>
    - data import documentation at <http://bycon.progenetix.org/importers/>
* revision of `importTablesGenerator.py`

### 2024-10-17 (v2.0.2)

* added a `ontologymapsReplacer.py` service app to (re-) create the `_byconServicesDB.ontologymaps` collection
    - this uses the now extended `OntologyMaps` class
* fixed the `schemas` service (recently broken during path parsing refactoring)

### 2024-10-10 (v2.0.1)

* bug fix for query generation for `/datasets` endpoint where `testMode=true`
  pragma wasn't interpolated towards alternative response entities
    - test with <https://progenetix.org/beacon/datasets/progenetix/biosamples/?testMode=true>
* clean up of location and handling of configuration files => both for the package
  and local installs
    - renamed `bycon/definitions` back to `bycon/config` since no other local
      configs in the package anymore
    - removed the previous duplication of local configs since now consistent
      hierarchy both for local scripts in the project directory as well as in the
      web server context (_i.e._ the `local` directory is at the same level so
      local references work)
    - removed `install.yaml` and point to `local/env_paths.yaml` during installations
      so that no double definition of local paths is needed

### 2024-10-10 (v2.0.0 "Taito City")

#### General Summary

The 2.0.0 version of `bycon` represents a milestone release where a general
updated project structure and code base has been established. The main changes involve:

* re-integration of utility functionality into the project
    - `byconServices` => `housekeepers` => `importers` => `rsrc` have been (re-)integrated
      from `byconaut`
    - similarly => `byconServiceLibs` are now part of the `bycon` libraries
* re-structuring of the `beaconServer` apps and calling
    - all general Beacon functions in `bycon` are now invoked from a few
      classes which correspond to the Beacon response types
* (ongoing) deprecation of non-standard parameters and functions

#### Recent Additions

* rewrote path parsing and entity selection
    - added `path_id_value_bycon_parameter` to map the REST path `{id}`
      to a parameter name (e.g. `biosampleId` or `filters` for some services); this removes the separate processing of `request_entity_path_id_value`
      later on
* moved more service functions into dedicated modules; most of the service "apps"
  now just call the response modules/functions
    - this might led to a future removal of the separate apps/module files
      and adding the calls directly to `services.py` in the near future...

### 2024-09-30 (v 1.9.8)

* general refactoring of the calling from the `beacon.py` app
    - remval of all the dedicated caller modules (e.g. `datasets.py` => `filtering_terms.py` ...)
      which are now just called by there response functions
* more code streamlining for `byconServices` apps
    - mostly removal of executable status
    - more removal of functions from main modules (e.g. `ontologymaps` now uses a
      separate `OntologyMaps` class in a library module)

### 2024-09-25 (v 1.9.7)

* **BUG FIX**: CNV statistics accessible through the `progenetix.org/services/cnvstats`
  endpoint had been broken for a while => delivering wrong CNV coverage values.

### 2024-09-25 (v 1.9.6)

* fixes: some broken apps due to incomplete library referencing after update

### 2024-09-24 (v 1.9.5)

* refactoring of service library loading
    - the main `bycon/__init__.py` now pre-loads the `byconServices` libraries
* renaming of `services` to `byconServices`
    - for the web server the `byconServices` files are still copied to `services`

### 2024-09-19 (v.1.9.4)

* `byconaut` => `bycon` refactoring
    - move of many "mature" utility functions from `byconaut` into the `bycon`
      repository following the previous `services` move
        * `housekeepers`
        * `importers`
* move of the `ontologymaps` and `publications` collections from `progenetix`
  to `_byconServicesDB`
    - clearer separation between "Beacon core" and "additional services"
```
use admin
db.runCommand(
    {
        renameCollection: 'progenetix.ontologymaps',
        to              : '_byconServicesDB.ontologymaps'
    }
);
db.runCommand(
    {
        renameCollection: 'progenetix.publications',
        to              : '_byconServicesDB.publications'
    }
);
```

### 2024-09-13 (v.1.9.3)

* services moved to bycon from byconaut

## Changes Archive

Changes before the `byconaut` re-fusion are [kept here](changes-archive).

## To Do

### Upcoming

* VRS 2.n support employing `vrs-python`

### Long Term Plans

* retire `byconServiceResponse` for aggregation response (which is
  under cdevelopment in 2.n)
