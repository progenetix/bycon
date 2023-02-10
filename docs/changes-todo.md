---
title: Changes & To Do
---

## Changes 

### 2023-02-05

* `bycon` now available as Pypi package
    - `pip install bycon`

### 2023-01-15

- [x] create bycon documentation subdomain & configure Github pages for it  

## Bugs & TODO

* [ ] disentangle general configurations, resources (which stay with the package)
  and instance-specific ones and load them from their appropriate locations
    - `beaconServer` and `services` scripts need to (over-) load from configs
      within their directories
    - this is in principle already possible, just need disentanglement etc.
* [ ] Data: fix publication data for consequent inclusion of `ISO3166alpha2` codes
* [ ] fix publications.py default filters "PMID" and "genomes:>0"
