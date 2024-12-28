# Welcome to the `bycon` and `beaconPlus` project documentation

## Bycon - a Python-based environment for the Beacon v2 genomics API

The `bycon` project - at least at its current stage - is a mix of _Progenetix_ (i.e. GA4GH object model derived, _MongoDB_ implemented) - data management, and the implementation of middleware & server for the Beacon API.

Some features and pecularities of the `bycon` solution are: 

* A single install can host multiple beacons and multiple datasets
  and those can be intersected.
* `bycon` handles Beacon queries with full model aggregation; it does not
  matter which endpoint and response entity are combined with what
  type of filter or variant parameter since always all entities are evaluated
  and the response is aggregated. A single query can include parameters for an
  individual's sex, the histoloical diagnosis of a biosample, an experimental
  platform and genomic variation parameters and the response can deliver
  biosamples, individuals ... matching all those parameters.
* With its origin in the Progenetix resource ("beaconized" since 2016) 
  `bycon` provides strong support for copy number variation data, including
  additional services such as CNV frequency plots for matched results or
  various file export formats beyond the standard JSON response.
* We provide several front-end projects of which the basic ([BeaconPlus](/beaconplus)) is a general version and since 12/2024 is being distributed as part of the `bycon` package.


!!! info "Bycon Code"

    The `bycon` code is maintained in the [`progenetix/bycon` repository](http://github.com/progenetix/bycon/). Some additional utility scripts & functions can be found in the
    [`byconaut`](http://github.com/progenetix/byconaut/) repository but are so not (well) documented & may contain deprecated or "internal use" code.

More information about the original use _Progenetix_ case can be found [on the project's documentation site](https://docs.progenetix.org/).

For more information about `bycon` installation and use please see [installation](./installation)
and track the [changes](./changes) for updates (or getting insights into the developments
leading to the current state).

## Notes about Previous Development

The `bycon` package was started during the development of the [**Beacon v2**](https://docs.genomebeacons.org)
specification with the aims to a) test and demonstrate features of the emerging
specification in a real-world use case while b) serving the needs of the [Progenetix](https://progenetix.org)
oncogenomic resource. Many of the recent changes are aimed at disentangling
the code base from this specific use case.

An earlier version of the Progenetix && Beacon "BeaconPlus" stack had been provided
through the Perl based [**PGX** project](http://github.com/progenetix/PGX/).



