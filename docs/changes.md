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

### Recent

#### 2023-08-16 (v.1.1.4 => v1.1.5)

* some changes to defaults & mappings parsing
    - merging content of "beacon_defaults" & "service_defaults" (if existing) files
      during init into "beacon_defaults"
    - same for "beacon_mappings" & "service_mappings"
    - **new requirement**: `deepmerge` (removed `pydeepmerge)`)
* some reshuffling/fixes of entry type defaults
* refined `GeoLocation` schema - now in model...common and referenced there
* v1.1.5 was a bugfix immediately after the update ...

#### 2023-08-11 (v.1.1.2 -> 1.1.3)

* move the new `histoheatplot` method code to use ImageDraw instead of SVG raw
  for the heat strips (_i.e._ base64 encoded individual PNG strips)
    - e.g. reduces size of 9.3MB example to 188kB
* 1.1.3 fixes a combination query bug

#### 2023-08-10 (v.1.1.1)

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
    - `variant_parameters` and `variant_type_definitions` config files from
      `variant_definitions` (separating the query config from the type mappings)
    - `cytoband_utils` => `genome_utils`
    - `generate_genomic_mappings` wrapper for cutoband and interval functions
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
  - `analysis_info: { experiment_id: 'geo:GSM498847', series_id: 'geo:GSE19949' }` leads to `{server_callsets_dir_loc}/GSE19949/GSM498847/{callset_probefile_name}`
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
