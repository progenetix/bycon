# Upcoming & To Do

## Future Plans

These plans will be revealed ... in the future.

## Bugs & TODO

* [ ] clean & reduce handovers, e.g. do not provide handovers for sample variants
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
