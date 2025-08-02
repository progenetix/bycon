[![License: CC0-1.0](https://img.shields.io/badge/License-CC0%201.0-lightgrey.svg)](http://creativecommons.org/publicdomain/zero/1.0/)

# Bycon - a Python-based full stack environment for the Beacon genomics API

The `bycon` project implements a data hosting environment for genomic and pheno-clinical data aligned with the GA4GH Beacon data model. It provides a Beacon API for data query and retrieval but also has extended functionality with a focus on genomic copy number variation data. For a prominent implementation example showcasing `bycon` features please see the [*Progenetix* oncogenomic resource](https://progenetix.org).

The underlying database system utilizes a _MongoDB_ instance and a storage model following for the most part the GA4GH object model.

Additionally, the `bycon` project implements functions for the ingestion and management of  genomic variants and phenoclinical data,
and provides a front end for the Beacon API as a statically compiled React project
("beaconPlus"). An instance of the _beaconPlus_ front end is accessible at [beaconplus.progenetix.org](https://beaconplus.progenetix.org).

## More Documentation

Documentation has been moved to [`bycon.progenetix.org`](http://bycon.progenetix.org).
Due to the rapid code development it is recommended to keep following the [Changes](http://bycon.progenetix.org/changes/)
page.

## Installation

The installation is documented [`on the website`](http://bycon.progenetix.org/installation/)
(and in the page's Markdown [source here](./docs/installation.md)).
