---
title: Changes & To Do
---

## Changes

### 2023-03-31 (v1.0.26)

* removal of VRS classes since VRS is about to switch to EFO
* added `EFO:0020073: high-level copy number loss` from the upcoming EFO release
* adding `examplez` dataset definition

### 2023-03-30 (v1.0.25)

Bug fix release:

* fixed `output=text` errors
* some argument parsing bugs that crept in with last release
* library re-shuffling w/ respect  to `byconaut`

### 2023-03-27 (v1.0.24)

* added `output=vcf` option for variant export & made it default for the 
`phenopackets` entity
    - VCF export is basic & hasn't been tested for round trip compatibility
* added filter exclusion flag:
    - for POST a Boolean `"excluded": true`
    - for GET prefixing a term by an exclamation mark (e.g. `!PATO:0020002`)
    - this is a **BeaconPlus** feature - see [issue #63](https://github.com/ga4gh-beacon/beacon-v2/issues/63) in `beacon-v2` 

### 2023-03-02 (v1.0.22)

* v1.0.22 fixes the `testMode=True` call

### 2023-02-05

* `bycon` now available as Pypi package
    - `pip install bycon`

### 2023-01-15

- [x] create bycon documentation subdomain & configure Github pages for it  

## Bugs & TODO

* [x] disentangle general configurations, resources (which stay with the package)
  and instance-specific ones and load them from their appropriate locations
    - `beaconServer` and `services` scripts need to (over-) load from configs
      within their directories
    - this is in principle already possible, just need disentanglement etc.
* [ ] Data: fix publication data for consequent inclusion of `ISO3166alpha2` codes
* [ ] fix publications.py default filters "PMID" and "genomes:>0"
