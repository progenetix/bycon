# Changes & To Do

## Notes about Previous Development

The `bycon` package was started during the development of the [**Beacon v2**](https://docs.genomebeacons.org)
specification with the aims to a) test and demonstrate features of the emerging
specification in a real-world use case while b) serving the needs of the [Progenetix](https://progenetix.org)
oncogenomic resource. Many of the recent changes are aimed at disentangling
the code base from this specific use case.

An earlier version of the Progenetix && Beacon "BeaconPlus" stack had been provided
through the Perl based [**PGX** project](http://github.com/progenetix/PGX/).

## Changes Tracker

### 2023-04-03 (v1.6.5)

#### Multi-variant matches first pass

We now implement an experimental version of multi-variant matching, to retrieve
samples which show co-occurrence of 2 or more variants. This so far is limited to
a few parameters:

* NEW: `variantQueryDigests` in the form of `9:9000001-21975098--21967753-24000000:DEL`
    - several of those can be comma-concatenated
    - probably not final name or format
    - only bracket matches & ranges working (but will change ...)
    - different variant types can be used
* `geneId` has been morphed to a list parameter (though keeping the standard name)
    - usual comma-concatenation etc.
    - here only a global `variantType` can be provided
* future versions to implement mixed matches etc. (e.g. sequence variant & CNV)

#### Other ...

* fixed paginated handovers missing the `info.content_id` parameter which is used
  by the progenetix-web etc. front ends
* changed the `cytoBands` argument to `type: array`, to allow definition of multiple
  cytogenetic regions, e.g. to indicate fusions or bracket requests
    - this might be a temporary solution for testing purposes and e.g. replaced
      by a future parsing of simple statements like `t(8;14)(q24;q32)`
* moved some cytoband functionality to the main `bycon` package, from `byconaut`,
  to allow processing of cytoband requests in the main Beacon service
* `byconaut` was restructured for exacutables, with `housekeepers` and `importers`
  directories

### 2024-03-25 (v1.6.4)

* added `scopes` to `beacon/filtering_terms/`
    - see <https://github.com/ga4gh-beacon/beacon-v2/pull/118>
* fixed bug where the default splitting of input parameters by comma led to over-splitting
  of the "embedded list" values in `plotPars` (e.g. using `plotPars=plotGeneSymbols=MYC,T,TP53`
  would lead to `plotPars=plotGeneSymbols=MYC::T::TP53` ... and later errors)
    - now "non-list" strings w/ internal `,` are just re-joined & a warning is created

### 2024-03-07 (v1.6.3)

* configuration changes:
    - `beacon_defaults` file changed to `entity_defaults` since only entities
      defined in it
    - paths are now defined within the entity definitions, no separate aliases etc.
    - local overrides for the Beacon entity defaults now in `local/instance_overrides.yaml`
    - for byconaut a separate `services_entity_defaults` file provides the additional
      services (e.g. `sampleplots` ... pseudo-entities)

### 2024-03-07 (v1.6.2)

* adding a `__collections_response_remap_cohorts(self, colls=[])` function
  to reformat the collections response for cohorts from the collations format
    - TODO: define cohorts as separate entities which are read in during collations
      generation, with their additional parameters etc.
* fixed the openAPI endpoints for collation responses (datasets & cohorts); are
  [incorrect in current Beacon spec.](https://github.com/ga4gh-beacon/beacon-v2/issues/116)
* bug fix `byconaut`: matrix export was broken since 1.6.1
* exception capture for wrong form values: string values of "None", "none", "Null",
  "null" from GET requests are now converted to logical `None` (i.e. removed)

### 2024-03-06 (v1.6.1)

* bug fix: individuals & phenopackets endpoints were broken in 1.6.0 due to missed
  clean up in query code
* bug fix `byconaut`: vcf & pgsxseg exports were broken in 1.6.0 due to incomplete
  clean-up of internal variant mapping
* bug fix `byconaut`: `/geolocations` queries were broken due to needed setting of
  authorization / granularity, which was handled by `run_beacon_init_stack` which
  however wasn't used by this service
* global change: removal of `run_beacon_init_stack` and inclusion of its
  function calls in the ubiquitous `initialize_bycon_service`

### 2024-03-04 (v1.6.0)

* simplification of internal parameter processing
* `bycon` / `byconaut` - new method "variantsbedfile"
    - takes over for the previous bedfile/UCSC variants handover generation (removed
      from `handover_generation`)
    - defaults to bedfile download from variant query
    - `output=ucsclink` creates the UCSC link with added bedfile payload
* `byconaut` - refactoring of `frequencymapsCreator.py` to use the standard collation
  bundle generation instead of custom queries 
* `byconaut` - change of collation retrieval to work now with `collationTypes`
  parameter
    - this allows to e.g. get all clustered CNV plots for a classification tree:
        * `/services/collationplots/?collationTypes=NCIT&minNumber=200`
* bug fix: broken server address in handovers
* bug fix: `id` specific query for collations was broken (delivered all)
* bug fix: mapping of basic chromosome ids (`9`) to refseqs was broken

### 2024-02-24 (v1.5.2)

* new `instance_overrides.yaml` config document in `local`
    - this allows to override Beacon instance parameters based on
      the URL the service is running under, enabling multiple Beacon
      instances per server
* new `analysis_operation` in `analyses` (_i.e._ "pgxAnalysis" in Progenetix
  database model) allows now the filtering of analyses based on the type of
  genomic profiling performed with its (so far) values:
    - `"analysis_operation.id":"EDAM:operation_3961",
      "analysis_operation.label":"Copy number variation detection"`
    - `"analysis_operation.id":"EDAM:operation_3227",
      "analysis_operation.label":"Variant Calling"`

### 2024-02-21 (v1.5.1)

* `BYC_PARS` now as a global parameter, not passed around in methods (formerly
  `byc["form_data"]`)
* byconaut: fix of parsing of plot variables (which can be shown through
  `&showHelp=true`)
* hot fix: added "protected" status for `external_references` in general empty
  field clean-up since the object is required by the front-end (even if empty list)

### 2024-02-20 (v1.5.0)

* refactoring global configs into `bycon/config.py` to slowly get rid of some of
  the `byc` -> ... imports  (e.g. global DB parameters, collecting warnings...)
* removal of `service_config` parameter & generator code from `bycon`, nof handled
  explicitely in the different byconaut services
* fixed `geneVariantRequest` to be selected as type when a `geneId` parameter is
  provided
* fixed handovers for non-default datasets by adding the `datasetIds` parameter
  to the handover
    - bug was based on older design retrieving the dataset id directly from the
      handover in the temp storage ...
* moved (partially so far) `external_references` to `references` in biosamples
    - reference objects are now standard `id`, `label` term objects
    - `references` is an object, i.e. the items are keyed `{"pubmed": {"id": "PMID:1234567", ...`
    - regeneration of the reference structure from Beacon/Phenopackets is done at export time
* `byconaut` with new `/services/samplemap/` endpoint for plotting geolocations
  of sample data after standard Beacon query
* `filter_definitions`
    - fix for arrayexpress series processing (now `AEseries`)
    - changed `collatiionType` `PMID` => `pubmed`
* fixed `uploader` fail due to missing import

### 2024-02-07 (v1.4.2)

* more consolidation of argument/cgi parsing libraries
* filter flag parameters now properly defined in `argument_definitions.yaml`
* use of a common `db_config` object for database configuration parameters
* piecemeal move of placeholder parameters from `config.yaml` (either
  through removal & fallbacks in methods, or through definition in
  `argument_definitions`)
* working on error responses...
* removed generic pre-processing methods for error & general responses
* fixed a bug which allowed non-matching filters to pass
* fixed examples in `tests`
* fixed `POST` processing (wrong `filters` nesting as in examples ...)
* fixed the OpenAPI "endpoints" info for the entry types
    - The `openAPIEndpointsDefinition` parameter in http://progenetix.org/beacon/map/
      should now point to working definitions per entity, e.g.
      https://progenetix.org/services/endpoints/biosamples

### 2024-02-02 (v1.4.1)

* new `ChroNames` class for accessing chromosome and refseq ID mappings (still utilising
  `byc["refseq_chromosomes"]` as input, read during init from `rsrc/.../refseq_chromosomes.yaml`)
* `byconaut`: Added a new `plotType=histosparklines` plotting option. It basically modifies
  `plot_defaults` parameters for minimal histoplots (no border, no background, small
  and narrow), e.g. for use in mouse-overs or in tables
    - one can still override those parameters, e.g. with `&plotPars=plotDendrogramWidth=50::plotAreaHeight=32`
![](https://progenetix.org/services/collationplots?filters=pgx:icdom-85003,pgx:icdom-81703,pgx:icdom-80703,pgx:icdom-87003&plotType=histosparklines)
![](https://progenetix.org/services/collationplots?filters=pgx:icdom-85003,pgx:icdom-81703,pgx:icdom-80703,pgx:icdom-87003&plotType=histosparklines&plotPars=plotDendrogramWidth=50::plotAreaHeight=32::plotAreaOpacity=0.5)
* `byconaut`: added option to use sequence id values for plotPars.plot_chros, e.g. `plotPars=plot_width=980::plotChros=NC_000023.11`
* fix: a `g_variants` endpoint w/o any parameter led to a query error
* removal of some `byconaut` code remnants
* some internal reshuffling; e.g. move of export/print helpers to from `cgi_parsing`
  to `beacon_response_generation` and `bycon_helpers`

### 2024-01-18 (v1.4.0)

* fix of `plotType` parameter as separate one (used in byconaut)
* fix of wrong parameter mapping for `geo:GSM....` filters
    - filter definition still pointed to `external_references.id` instead of
      `analysis_info.experiment_id`
* `byconaut`: move to general use of `byc["form_data"]` for arguments (_i.e._
  requiring the command line arguments to have been parsed into this object)
* fixed the `byconaut` `cytomapper` service by adding `cyto_bands` and `chro_bases`
  to the list of `variant_pars`

### 2024-01-10 (v1.3.9)

Bugfix release. Some default values provided in `argument_definitions.yaml`
file were overriding pre-processed values, leading to e.g. to an
endless loop in the handover generation.

### 2024-01-09 (v1.3.8)

* argument parameter redesign
    - definition of all parameters/arguments (web & local) in `argument_definitions.yaml`
    - parameters not defined there will not be processed anymore (however, there are some
      placeholders like e.g. `mode` or `key` which are not utilized by standard methods
      and can be co-opted for custom inputs)
    - plot parameters are provided as a single string to `plotPars`, with individual
      parameter pairs concatenated by `::`
        * in GET: `plotPars=plot_chros=8,9,17::labels=8:120000000-123000000:Some+Interesting+Region::plot_gene_symbols=MYCN,TP53,MTAP,CDKN2A,MYC,ERBB2::plot_width=800`
        * in CMD: `--plotPars "plot_chros=8,9,17::labels=8:120000000-123000000:Some Interesting Region::plot_gene_symbols=MYCN,TP53,MTAP,CDKN2A,MYC,ERBB2::plot_width=800"`
* modification of the `prdbug` helper

### 2023-12-18 (v1.3.7)

* added handling for user specific granularity permissions
    - so far `user_name` is just taken from a form parameter and then stored
      as `byc` root parameter (through `set_user_name`)
    - local processing (`env`) sets this to `local` (and has a default `record`)
      granularity
    - dataset specific, user specific maximum granularities can be set in
      `authorizations.yaml` which can be extended / overwritten from settings in
      `local/authorizations.yaml` (similar to `beacon_defaults.yaml` etc.)
    - future updates are planned to handle proper interpretation of `user_name`
      and proof of authorization...
* configuration: the basic parameters from `config.yaml` are now stored as `byc`
  root parameters and not kept in a mix of root & `config`

### 2023-11-20 (v1.3.6)

* modified `BeaconDataResponse` to keep the `resultSetsResponse` structure while
  remobving the `results` from each set, to allow resuult set specific handover 
  delivery (labeled as __CUSTOM__)
* moved all cytoband library code into `byconaut` (__FUTURE__ considerations for
  this in case Beacon supports cytobands ...)
* `byconaut` plots now directly use the database saamples format for plotting variants,
  w/o going through the canonical variant creation (this incurred a **huge** penalty)
* reminder that `byconaut` plots use the `plotType` parameter instead of `output`
* `byconaut` now has a color code mapping for the different (EFO, DUP/DEL ...) variant
  types; this allows to assign custom `plot_dup_color` etc. parameters while keeping
  the available variant types (`variant_state.id`) separated (see `byconaut -> local.plot_defaults`)

### 2023-11-17 (v1.3.5)

* more removal of non-standard components into `byconaut`, e.g. for file generation
  such as `.pgxseg`
* adding experimental `target` field to items in `filtering_terms` response
* adding `aminoacidChange` and `genomicAlleleShortForm` to request parameters
  (this was a bug fix - they were already activated but not in the `.json` version)

### 2023-10-31 (v1.3.4)

This update is mostly addressing the further removal of methods specific for
"beyond Beacon" functionality (e.g. variant binning and calculations for CNVs, plotting ...).

### 2023-10-25 (v1.3.3)

Most of the "special outputs" code has been moved to byconaut -> services.
For legacy reasons (e.g. use by pgxRpi) the webserver configuration needed some
rewrites ... They only apply for the Progenetix use case and are not needed if
sticking to the Beacon formats or if following the use of the new apps like
`services/vcfvariants`). Our (temporary) mappings are:

```
RewriteEngine On

# The following rules are for backward compatibilitty with pgxRpi before Oct 2023

RewriteCond %{QUERY_STRING} ^(.*?output=\w*?table.*?)$
RewriteRule "^/beacon/biosamples.*?$" /cgi-bin/bycon/services/sampletable.py?%1&responseEntityId=biosample [PT]

RewriteCond %{QUERY_STRING} ^(.*?output=\w*?table.*?)$
RewriteRule "^/beacon/individuals.*?$" /cgi-bin/bycon/services/sampletable.py?%1&responseEntityId=individual [PT]

RewriteCond %{QUERY_STRING} ^(.*?output=\w*?table.*?)$
RewriteRule "^/beacon/individuals.*?$" /cgi-bin/bycon/services/sampletable.py?%1&responseEntityId=individual [PT]

RewriteCond %{QUERY_STRING} ^(.*?output=\w*?matrix.*?)$
RewriteRule "^/beacon/analyses.*?$" /cgi-bin/bycon/services/samplematrix.py?%1&responseEntityId=analysis [PT]

RewriteCond %{QUERY_STRING} ^(.*?output=vcf.*?)$
RewriteRule "^/beacon/biosamples/([^/]+?)/g_variants.*?$" /cgi-bin/bycon/services/vcfvariants.py?%1&biosampleIds=$1 [PT]

RewriteCond %{QUERY_STRING} ^(.*?output=pgxseg.*?)$
RewriteRule "^/beacon/biosamples/([^/]+?)/g_variants.*?$" /cgi-bin/bycon/services/pgxsegvariants.py?%1&biosampleIds=$1 [PT]
```

### 2023-10-20 (v1.3.2)

This version removes the complete `bycon_plot` code (_i.e._ moves it to `byconaut`).
It still needs the further disentangling of the other alternative response options
(`.pgxseg`, `.pgxmatrix` ...) from the resultsets generation; this soon will follow
blueprint of the plot code removal.

**CAVE** Now all plotting options have been shifted to the `/services/collationplots`
and `/services/sampleplots` entry points.

### 2023-10-20 (v1.3.1)

This version provides another step in moving "non-standard" Beacon responses tp
the `byconeer` project. 

* creatiing a `.../services/sampleplots/` entry point which will be used to handle
  the sample (strips/clustered; histoplots from search results ...) web plotting
  instead of adding the `output=histoplot` etyc. option to standard Beacon queries
    - plot types can now be specified through `plotType=samplesplot` etc.
* some class (`ByconResultSets`) restructuring to allow plot outputs (this will be
  changed further, probably moving the whole plot ... classes and methods to `byconeer`)

### 2023-10-12 (v1.3.0)

This is an extensive internal code update which

* moves service response generation to byconaut (implemented as `ByconautServiceResponse`
class w/ its methods)
* removes many of the methods from `service_utils` since they have been implemented
in the beacon or services response classes and (mostly) limits the library to
general/initialization methods (still more to clean...)
* fixes some inconsistencies (e.g. snake vs. camel cases in paths where sometimes
non-standard versions were documented - now using the Beacon v2 defaults such as
`beacon/filtering_terms/` instead of `beacon/filteringTerms/`)
* similar for geo queries (e.g. `geoLatitude` as query parameter instead of `geolatitude`)
 though this is "BeaconPlus" anyway

**CAVE**: These changes also affect the front-ends (`progenetix-web`, `beaconplus-web` etc.)
which need to be recompiled from the latest versions

### 2023-08-30 (v1.2.2)

* some defaults cleaning (e.g. removal of non-standard paths from built in `beacon_defaults`)

### 2023-08-25 (v1.2.1)

* clean-up of info response m(all entryType schemas shown now)
* modification of entity_defaults format
* use of `beaconCollectionsResponse` for services & deprecation of `ProgenetixServiceResponse`
* `mongo_test_mode_query` (needs to be propagated more...)
* `beaconplus` domains support

### 2023-08-22 (v1.2.0)

* fix of `filterLogic` parameter for forced global `$or`
* more reshuffling of defaults and config parameters
    - merged `beacon_mappings` intop `beacon_defaults`
    - moved `config.yaml` to `bycon/config/`
    - splitting of the `beacon_defaults` parameters into standard parameters, e.g.
      for the main entry types, into the `beacon_defaults.yaml` file in
      `bycon/config/`, and custom parameters (e.g. Progenetix' `phenopackets` entry
      type definition or some aliases) into the `/local/` location
* streamlining of `__init__.py` and `read_specs.py` w/ respect to those changes
* concurrent `byconaut` update

#### 2023-08-21 (v1.1.7)

This update continues with the disentangling of "package inherent" defaults and
definitions and "local" ones. Partcullarly:

* standard Beacon entity definitions arte now part of the package configuration,
  _i.e._ `bycon/config/beacon_defaults.yaml` has now the entities, and additional
  entities are then provided from `bycon/local/beacon_defaults.yaml` (which is copied
  from the project root `/local/beacon_defaults.yaml`) during `updev.sh`)
    - examples are the Progenetix specific data in the `info` entity or the non-standard
      `phenopackets` entry type
* similar for `dataset_definitions` ...

#### 2023-08-21 (v1.1.7)

This update continues with the disentangling of "package inherent" defaults and
definitions and "local" ones. Partcullarly:

* standard Beacon entity definitions arte now part of the package configuration,
  _i.e._ `bycon/config/beacon_defaults.yaml` has now the entities, and additional
  entities are then provided from `bycon/local/beacon_defaults.yaml` (which is copied
  from the project root `/local/beacon_defaults.yaml`) during `updev.sh`)
    - examples are the Progenetix specific data in the `info` entity or the non-standard
      `phenopackets` entry type
* similar for `dataset_definitions` ...

#### 2023-08-16 (v1.1.6)

* bugfix release for service items

#### 2023-08-16 (v1.1.4 => v1.1.5)

* some changes to defaults & mappings parsing
    - merging content of "beacon_defaults" & "service_defaults" (if existing) files
      during init into "beacon_defaults"
    - **new requirement**: `deepmerge` (removed `pydeepmerge)`)
* some reshuffling/fixes of entry type defaults
* refined `GeoLocation` schema - now in model...common and referenced there
* v1.1.5 was a bugfix immediately after the update ...

#### 2023-08-11 (v1.1.2 -> 1.1.3)

* move the new `histoheatplot` method code to use ImageDraw instead of SVG raw
  for the heat strips (_i.e._ base64 encoded individual PNG strips)
    - e.g. reduces size of 9.3MB example to 188kB
* 1.1.3 fixes a combination query bug

#### 2023-08-10 (v1.1.1)

* services: new frequency plot type `histoheatplot`:
    - also some new related parameters, e.g. `plotHeatIntensity`
    - [/services/intervalFrequencies/?datasetIds=progenetix&filters=NCIT:C,!NCIT:C3247,!NCIT:C3510&filterPrecision=start&withSamples=500&collationTypes=NCIT&output=histoheatplot&plotAreaHeight=20&plotRegionGapWidth=&plotChros=3,17&plotHeatIntensity=1.5&plotGeneSymbols=TP53,BCL6&plotDendrogramStroke=2](http://progenetix.org/services/intervalFrequencies/?datasetIds=progenetix&filters=NCIT:C,!NCIT:C3247,!NCIT:C3510&filterPrecision=start&withSamples=500&collationTypes=NCIT&output=histoheatplot&plotAreaHeight=20&plotRegionGapWidth=&plotChros=3,17&plotHeatIntensity=1.5&plotGeneSymbols=TP53,BCL6&plotDendrogramStroke=2)
* `intervalFrequencies` now supports start-anchored greedy term matches as well
  as exclusion of individual terms through `!` prefix (as for normal filter searches)

#### 2023-08-09 (v1.1.0)

* fixed gene position queries (had hardcoded `progenetix` database ...)
* general overhaul of query generation
    - `class ByconQuery`
    - called directly in `query_execution`
    - removed some variant query types (e.g. "type only")
    - better handling of `id` type queries (including the retrieval of the associated
      variants)
    - move to collection of query objects per entity instead of collection (is
      mostly a logical change for general use of entities instead of the database
      impolementation as target - that is resolved at the query execution)
    - TODO: probably will move from the dynamic variant query type detection
      to a stacked "test one after the other with hard-coded parameter checks"
      just for sanity reasons - but right now see above
    - TODO: variant requests and request type detection still not part of class
    - TODO: geo queries into class ...
* there is now a `force_empty_plot` (forceEmptyPlot) parameter so that sample
  queries w/o any CNV (e.g. from cancercelllines.org samples) generate an empty
  strip, to add non-CNV as labels
* fixed error in `interval_utils` (renamed config key...)
* fixed associated `byconaut` errors

#### 2023-07-26 (v1.0.72)

* cleaning of handovers
    - no "all variants from matched biosamples" ... anymore due to performance
      problems
    - now variant storage and handovers only for matched variants - _i.e._ if
      there was a variant query - _or_ if a sample, individual ... had been requested
      by path id
* CNV VCF fix
* some general handover creation cosmetics
* VRS schema components moved

#### 2023-07-25 (v1.0.71)

* finished the `ByconVariant` `vrsVariant` method and implemented this as the format
  for the Beacon variant response
* added sorting to `.pgxseg` files
* added compact `VRSallele` and `VRScopyNumberChange` schemas & using them in
  `ByconVariant(byc).vrsVariant(v)`

##### `byconaut`

* moved `geomap_utils` to `byconaut/services/lib`
* improved index generation for `2dsphere` indexes
* moved `geolocs` to `_byconServicesDB` and adjusted code accordingly
* fixed `frequencyMapsGenerator` for the new database

#### 2023-07-24 (v1.0.70)

* refactored the VCF export into `exportfile_generation`
* minor pagination code cleanup

#### 2023-07-24 (v1.0.69)

* fixed datatable & pgxseg download error (introduced w. 1.0.68)
    - thanks to @ClmtHua in [#20](https://github.com/progenetix/bycon/issues/20)
* internal change of more consistant use of `genomicVariant` for variant entity,
  schema

#### 2023-07-23 (v1.0.68)

* first production version of `ByconVariant` class and consecutive retirement of
  `...vrsify` functions
* new defaults in `variant_type_definitions` per EFO type:
    - `dupdel_state_id`
    - `snv_state_id`
    - `VCF_symbolic_allele`
* fixed wrong parameter mapping of `alternate_bases` (introduced ... when?)
* docs: split changes & to dos...

#### 2023-07-19 (v1.0.67)

* fix `.pgxseg` file loader bug (thanks Huan Zhang!)
* starting `variant_mapping.py` for a consolidated `ByconVariant` class

#### 2023-07-13 (v1.0.66) 

* modified `return_filtering_terms_response` to parse over the collations from
  different datasets
    - [ ] check & streamline
* modified `retrieve_gene_id_coordinates` (some error catching)
* introduced `housekeeping_db: _byconHousekeepingDB` for `querybuffer` and `beaconinfo`
    - accordingly changed `byconaut`, e.g. housekeeping -> `beacon_info_coll` 
* changed `services_db: _byconServicesDB` for `genes`

#### 2023-07-11 (v1.0.65)

* streamlining of schema file parsing
    - the schema file root is now hard coded to `path.join( pkg_path, "schemas" )`
    - schemas are identified by their **unique** name (`beaconMap.json`)
      or patent dir / default combination (`.../biosamples/defaultSchema.json`)
    - ... which means those have to be unique
    - this removes all the schema path definitions from `config.yaml`

#### 2023-07-06 (v1.0.64)

* fixing camelCase / snake_case errors for `filteringTerms` & `genomicVariations`
  entry types (I hope; those came up in 1.0.62 after streamlining config parsing...)

#### 2023-07-06 (v1.0.63)

* cleaning up the install.py script
* fix in byconaut for local preferences when executing from local repo (where
  this lead to an empty stats database -> beacon errors...)

#### 2023-07-05 (v1.0.62)

* bug fix sample plots
* internal function re-organization (`initialize_bycon_queries` deprecated & replaced
  by `parse_filters` & `parse_variants`)
* also addition to the ENV config in byconaut

#### 2023-07-04 (v1.0.61)

* adding `BYCON_MONGO_HOST` environment variable to enable other MongoDB host than
  `localhost` (which remains fallback/default) - thanks @fliem for [#17](https://github.com/progenetix/bycon/pull/17)
* added `--noo-sudo` to install.py - thanks @fliem for [#19](https://github.com/progenetix/bycon/pull/19)
* more tweaking of configuration reading

#### 2023-06-30 (v1.0.59)

* fixed new bug in variant parameter parsing
* fixed wrong parsing of command line list arguments (e.g. `--filters`)
* `install.py` now adds the `/local` configurations to the `/bycon/beaconServer/local/`
  directory
    - execution of command line beacon has access to them (not only apps in the server)
    - files are removed by `/updev.sh` before packaghe build
* added some command line examples to [`installation.md`](/installation/)

#### 2023-06-28 (v1.0.58)

* extensive renaming/-shuffling, e.g.:
    - `refseq_chromosomes` now in `rsrc/genomes/grch38` (only grch38 so far but this
      is all we currently use...)
        * also `parse_refseq_file` and `__get_genome_rsrc_path` functions
    - `variant_request_definitions` and `variant_type_definitions` config files from
      `variant_definitions` (separating the query config from the type mappings)
    - `cytoband_utils` => `genome_utils`
    - `set_genome_rsrc_path` wrapper for cytoband and interval functions
* fix for file uploader issues
    - [ ] TODO: documentation on website & lazy loading (e.g. interpolating
      `sample` to `biosample_id`; maybe just use column order ...)


#### 2023-06-26 (v1.0.57)

* more disentangling of configuration between `byconaut/services` and `/bycon`

#### 2023-06-21 (v1.0.56)

* `info_db` => `services_db` parameter renaming
* fix of missing interpolation of query parameters into the response metadata

#### 2023-06-21 (v1.0.55): Removal of `/services`

* removed the `/services` part from the bycon package - it is now maintained
  in [`byconaut`](https://github.com/progenetix/byconaut/) with the local location being defined in `install.yaml`
* fixed some [tests](http://bycon.progenetix.org/tests/)

#### 2023-06-21 (v1.0.54)

* adding `normalize_pgx_variant`

#### 2023-06-13 (v1.0.53)

* now probe plotting as implemented with auto-path detection based on callset
  values
  - `analysis_info: { experiment_id: 'geo:GSM498847', series_id: 'geo:GSE19949' }` leads to `{server_callsets_dir_loc}/GSE19949/GSM498847/{probefile_name}`
  - example: [progenetix.org/beacon/biosamples/pgxbs-kftvkafc/?output=samplesplot&plot_chros=3,5,6,14](https://progenetix.org/beacon/biosamples/pgxbs-kftvkafc/?datasetIds=progenetix&output=samplesplot&plot_chros=3,5,6,14)

#### 2023-06-12 (v1.0.52)

* modified `handover_definitions` to follow the specification:
  - `handoverType` now as in spec, also using public identifier where possible
    (so far `"id": "EDAM:3016", "label": "VCF"` for all VCF h->0)
  - since now different handovers can have the same `handoverType.id` this required
    the addition of an `info.contentId` value for the frontend to disambiguate
* starting the work on the `arrayplot` (?) plot type, including a new method
  for getting probe file paths (not yet activated)
* several field changes in biosamples, to align w/ main Beacon v2 default schema:
  - `sampledTissue` => `sampleOriginDetail`
  - `description` => `notes`
  - `timeOfCollection.age` => `collectionMoment`

### 2023-06-06 (byconaut)

* moved MongoDB index generation to `housekeeping.py`
* started to organize actions in `housekeeping.py` w/ user prompts

#### 2023-06-05 (v1.0.51)

* fixed pgxseg file reader (broken reference_name ... parsing after recent chromosome fix)
* removed some publication libraries/schemas only used in byconaut

#### 2023-06-02 (v1.0.50)

* fixed missing chromosomes in `.pgxseg` exports
* age search now with 2 values possible (e.g. to set a range)

#### 2023-05-31 (v1.0.49)

* added `days_from_iso8601duration` method
* added in individuals `index_disease.onset.age_days` field
    - populated using the new method w/ a byconaut "housekeeping" script
* added a first `alphanumeric` filter type & parsing
* this enables now an age filter query, e.g. `filters=age:<=P35Y2D`

#### 2023-05-31 (v1.0.48)

* addresses VCF export bugs [#14](https://github.com/progenetix/bycon/issues/14),
  [#15](https://github.com/progenetix/bycon/issues/15) and
  [#16](https://github.com/progenetix/bycon/issues/16) (thanks [David](https://github.com/d-salgado)!)
* fixes some `null` value complaints from the Beacon verifier (thanks [Dmitry](https://github.com/redmitry)!)

#### 2023-05-26 (v1.0.47)

* changed handover id format from `pgx:handover:biosamples` to CURIE-compatible
  `pgx:HO.biosamples` etc. style (see Beacon [#83](https://github.com/ga4gh-beacon/beacon-v2/issues/83))

#### 2023-05-25 (v1.0.46)

* changed the internal schema for genomic variants
    - simplification, e.g. using everywhere `variantState` and flattening
      of the `location` object
    - adding `MT` chromosome support (though not necessarily for searches etc.)

#### 2023-05-24 (v1.0.45)

* `instantiate_schema` has been rewritten; this lead to a number of code adjustments
  (e.g. usually starting w/ the schemas themselves, _not_ w/ `properties` when
  instantiating) and bug fixes (mostly capturing errors from default "none" values)

#### 2023-05-22 (v1.0.44)

* code clean-up
  - removal of unnecessary "return" staements
  - re-structuring of `argument_definitions.yaml` in preparation for common
    parsing of input values

#### 2023-05-17 (v1.0.43)

* rewrite of `.pgxseg` processing into `ByconBundler` class
    - includes `callsets_variants_bundles` and `callsets_frequencies_bundles` for plot object generation
* plot labels fix for labels starting at the `0` base

#### 2023-05-12 (v1.0.41)

* complete refactoring of plot code as `ByconPlot` class
* renamed library `bycon_plot.py`

#### 2023-05-09 (v1.0.40)

* new `services/samplesPlotter` entry point
    - currently specific for file uploads (handling of DB calls see below)
* completed the integration of the new `bycon`  plotting 
* new `plotCytoregionLabels` plot labeling parameter
    - [/beacon/biosamples/?plotGroupBy=icdot&filters=pgx:icdom-95003&plotCytoregionLabels=8q,9p11p12&plotGeneSymbols=MYCN&output=histoplot&limit=500](http://progenetix.org/beacon/biosamples/?plotGroupBy=icdot&filters=pgx:icdom-95003&plotCytoregionLabels=8q,9p11p12&plotGeneSymbols=MYCN&output=histoplot&limit=500)

#### 2023-05-03 (v1.0.38)

* added method to subset samples for multi-histogram generation using the `groupBy`
  parameter for matching of `filter_definitions` classes
    - [/beacon/biosamples/?groupBy=icdot&filters=pgx:icdom-95003&plotGeneSymbols=MYCN&output=histoplot&limit=100](http://progenetix.org/beacon/biosamples/?groupBy=icdot&filters=pgx:icdom-95003&plotGeneSymbols=MYCN&output=histoplot&limit=100)
* removal of deprecated `cgitb` use & replacing it w/ a simple _Exception_/traceback
  wrapper
* expansion of the [plotting documentation](http://bycon.progenetix.org/plotting/)
* move of the plot arguments parsing to `cgi_parsing.py`

#### 2023-05-01 (v1.0.37)

* more plotting: now histograms and samples - if >3 - get a dendrogram to indicate
  the clustering results
    - clustering can be suppressed by `&plotClusterResults=false`

--------------------------------------------------------------------------------
### 2023 01-04

#### 2023-04-27 (v1.0.36)

* plotting & clustering of samples
    - [/beacon/analyses/?filters=pgx:icdom-95003&plot_labelcol_width=0&plot_filter_empty_samples=y&plotGeneSymbols=MYCN&plot_samplestrip_height=1&output=samplesplot&limit=500](http://progenetix.org/beacon/analyses/?filters=pgx:icdom-95003&plot_labelcol_width=0&plot_filter_empty_samples=y&plotGeneSymbols=MYCN&plot_samplestrip_height=1&output=samplesplot&limit=500)

#### 2023-04-27 (v1.0.35)

* new `custer_utils.py` library for cluster matrix generation and clustering
    - uses [`scipy.cluster`](https://docs.scipy.org/doc/scipy/reference/cluster.html)
    - first test implementation for frequency maps; auto-clusters if >2 using the
      concatenated gain and loss frequencies per standard binning
    - [x] tree plotting
* plot gene label refinement

#### 2023-04-25 (v1.0.35)

* more plot_utils goodness - staggered labels
    - [/services/intervalFrequencies/?plotChros=2,8,9,17&labels=8:120000000-123000000:Some+Interesting+Region&plot_gene_symbols=MYCN,REL,TP53,MTAP,CDKN2A,MYC,ERBB2,CDK1&filters=pgx:icdom-85003&output=histoplot](http://progenetix.org/services/intervalFrequencies/?plotChros=2,8,9,17&labels=8:120000000-123000000:Some+Interesting+Region&plot_gene_symbols=MYCN,REL,TP53,MTAP,CDKN2A,MYC,ERBB2,CDK1&filters=pgx:icdom-85003&output=histoplot)
    - [/beacon/biosamples/?datasetIds=examplez,progenetix,cellz&referenceName=9&variantType=DEL&start=21500000&start=21975098&end=21967753&end=22500000&filters=NCIT:C3058&output=histoplot&plotGeneSymbols=CDKN2A,MTAP,EGFR,BCL6](http://progenetix.org/beacon/biosamples/?datasetIds=examplez,progenetix,cellz&referenceName=9&variantType=DEL&start=21500000&start=21975098&end=21967753&end=22500000&filters=NCIT:C3058&output=histoplot&plotGeneSymbols=CDKN2A,MTAP,EGFR,BCL6)

#### 2023-04-20 (v1.0.34)

* new `geneSymbols` parameter for plot labeling allows to add gene labels to
  the position of a given gene on a plot
    - [http://progenetix.org/services/intervalFrequencies/?geneSymbols=MYC,ERBB2,CDK1&filters=pgx:icdom-85003&output=histoplot](/services/intervalFrequencies/?geneSymbols=MYC,ERBB2,CDK1&filters=pgx:icdom-85003&output=histoplot)
    - TODO: still needs a "no-overlap" shifting method for closely spaced labels (as in the Perl version...)

#### 2023-04-17 (v1.0.33)

* refinement of `histoplot` options; now as the standard for standard Beacon
  results by using the `&output=histoplot` pragma
    - [/beacon/biosamples/?datasetIds=examplez,progenetix,cellz&referenceName=9&variantType=DEL&start=21500000&start=21975098&end=21967753&end=22500000&filters=NCIT:C3058&output=histoplot](http://progenetix.org/beacon/biosamples/?datasetIds=examplez,progenetix,cellz&referenceName=9&variantType=DEL&start=21500000&start=21975098&end=21967753&end=22500000&filters=NCIT:C3058&output=histoplot)
* change of `histoplot` handover (`id: 'pgx:handover:histoplot'`) to use
  the plotting option instead of a redirect to the Perl `PGX` version

#### 2023-04-14 (v1.0.32)

* basic implementation of plot labels for the collation frequency plots,  using
  the `plot_region_labels` parameter
* switch of the cancercelllines.org UI to use this plotter instead of the Perl
  based PGX one (only for the pre-computed collations)

#### 2023-04-14 (v1.0.30)

* added `plot_utils.py` and `plot_defaults.yaml`; now there is a first method
  for plotting histograms
    - so far limited to CNV histograms of many or few whole chromosomes from
      pre-computed frequencymaps
    - no separate sevice so far; can be invoked from the `intervalFrequencies`
      service with added `&output=histoplots` pragma
    - so far no marker addition etc.
    - <http://progenetix.org/services/intervalFrequencies/?filters=pgx:icdom-85003,pgx:icdom-87003,pgx:icdom-81403&plotChros=7,8,9,13,17&plot_title=CNV+Comparison&output=histoplot&size_plotimage_w_px=800&plot_chro_height=18>

#### 2023-04-12 (v1.0.29)

* fixed broken dataset selection (bug introduced w/ v1.0.28)
* moved dataset parsing to separate library `lib/dataset_parsing.py`

#### 2023-04-11 (v1.0.28)

* fixed the filter processing where "correctly looking but not existing" filter
  patterns were pruned from the query instead of being kept & leading to a mismatch
* added 2 types of warnings for such cases:
    - undefined filter pattern
    - correct pattern but value not in database

#### 2023-03-31 (v1.0.27)

* FIX: `ids` service (and therefore identifiers.org resolver) was broken due to custom & degraded config path

#### 2023-03-31 (v1.0.26)

* removal of VRS classes since VRS is about to switch to EFO
* added `EFO:0020073: high-level copy number loss` from the upcoming EFO release
* adding `examplez` dataset definition

#### 2023-03-30 (v1.0.25)

Bug fix release:

* fixed `output=text` errors
* some argument parsing bugs that crept in with last release
* library re-shuffling w/ respect  to `byconaut`

#### 2023-03-27 (v1.0.24)

* added `output=vcf` option for variant export & made it default for the 
`phenopackets` entity
    - VCF export is basic & hasn't been tested for round trip compatibility
* added filter exclusion flag:
    - for POST a Boolean `"excluded": true`
    - for GET prefixing a term by an exclamation mark (e.g. `!PATO:0020002`)
    - this is a **BeaconPlus** feature - see [issue #63](https://github.com/ga4gh-beacon/beacon-v2/issues/63) in `beacon-v2` 

#### 2023-03-02 (v1.0.22)

* v1.0.22 fixes the `testMode=True` call

#### 2023-02-05

* `bycon` now available as Pypi package
    - `pip install bycon`

#### 2023-01-15

- [x] create bycon documentation subdomain & configure Github pages for it  
