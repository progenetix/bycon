# Upcoming & To Do

## Future Plans

The `bycon` package had been implemented specifically to a) drive and test run features
during Beacon protocol development, while b) serving the Progenetix use case.
This led to some overall complexity - keep Progenetix running w/ existing features
while testing `bycon` and also implement the whole Beacon code base while not
necessarily making use of all.

With a feature-rich but overly complex `bycon` package fulfilling those requirements
ongoing work startin in Spring 2023 mainly targets:

* disentanglement of non-Beacon code and Progenetix specific configuration from
  the package
* simplification of configuration and processing pipelines to the emerging practices
  of a "matured" Beacon v2 protocol

## Bugs & TODO

* [ ] create a new `beaconDataPipeline.py` app which runs all requests against the
  "data" entry types (_i.e._ `g_variants`, `biosamples`, `individuals`, `analyses`,
  `runs`) and simplify `beacon.py` to a pure remapper(?)
* [ ] add non-CNV variants to standard plots
* [x] clean & reduce handovers, e.g. do not provide handovers for sample variants
  (all variants for a sample can be downloaded through the REST path & sample id
  as `/biosamples/{id}/g_variants`, w/ optional `&output=pgxseg` etc.)
* [ ] consistant test suite as set of URLs & script for running over them / checkin
  the responses (e.g. `testMode` but also w/ queries...)
* [ ] flattening of the Progenetix database models w/ mapping methods for
  standard Beacon model output (& beyond, like Phenopackets)
    - using the "datatable_mappings" paradigm as now already implemented for the
      `ByconVariant` class
* [x] move the "services" collection to a generic `_byconServicesDB`
    - [x] no problem for `querybuffer` and `beaconinfo` which can be generated _ad hoc_
    - [x] other affected collections would be `genes` and `geolocs` which need to be moved => `_`
    - [x] special Progenetix project collections would have to be considered
      separately (e.g. w/ hard-coded `progenetix` db?): `publications` and `ontologymaps` => hard coded to `progenetix`
* [x] split installation method into separate parts for `beaconServer` and `services` (the latter then in `byconaut`)
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
