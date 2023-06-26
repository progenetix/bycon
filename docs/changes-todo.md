# Changes & To Do

## Changes

### Recent

#### 2023-06-21 (v1.0.57)

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
    - [/services/intervalFrequencies/?chr2plot=2,8,9,17&labels=8:120000000-123000000:Some+Interesting+Region&plot_gene_symbols=MYCN,REL,TP53,MTAP,CDKN2A,MYC,ERBB2,CDK1&filters=pgx:icdom-85003&output=histoplot](http://progenetix.org/services/intervalFrequencies/?chr2plot=2,8,9,17&labels=8:120000000-123000000:Some+Interesting+Region&plot_gene_symbols=MYCN,REL,TP53,MTAP,CDKN2A,MYC,ERBB2,CDK1&filters=pgx:icdom-85003&output=histoplot)
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
    - <http://progenetix.org/services/intervalFrequencies/?filters=pgx:icdom-85003,pgx:icdom-87003,pgx:icdom-81403&chr2plot=7,8,9,13,17&plot_title=CNV+Comparison&output=histoplot&size_plotimage_w_px=800&plot_chro_height=18>

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

## Bugs & TODO

* [ ] split installation method into separate parts for `beaconServer` and `services` (the latter then in `byconaut`)
* [x] add method to subset samples for multi-histogram generation
* [ ] option for summary histogram over? under? samplesplot
* [x] script for auto-generation of parameter documentation
* [x] fix filter queries for correct no-match:
    - query type indicates that the filter is "collationed"
    - query_generation looks for term in collations to perform term expansion
    - BUG: if term is not found -> currently term is not added to final query
      object -> query is only based on other parameters
* [x] disentangle general configurations, resources (which stay with the package)
  and instance-specific ones and load them from their appropriate locations
    - `beaconServer` and `services` scripts need to (over-) load from configs
      within their directories
    - this is in principle already possible, just need disentanglement etc.
* [ ] Data: fix publication data for consequent inclusion of `ISO3166alpha2` codes
* [ ] fix publications.py default filters "PMID" and "genomes:>0"
