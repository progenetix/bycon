[![License: CC0-1.0](https://img.shields.io/badge/License-CC0%201.0-lightgrey.svg)](http://creativecommons.org/publicdomain/zero/1.0/)

# Bycon - a Python-based environment for the Beacon v2 genomics API

The `bycon` project - at least at its current stage - is a mix of _Progenetix_ (i.e. GA4GH object model derived, _MongoDB_ implemented) - data management, and the implementation of middleware & server for the Beacon API.

In its current state the `bycon` package is undergoing a transition from resource
specific to general use environment. There is still some entanglement between
code and use case specific definitions (e.g. database definitions inside the
distribution) though this is (early 2023) in a process of "disentanglement".

## More Documentation

Documentation has been moved to [`bycon.progenetix.org`](http://bycon.progenetix.org).
W/ the rapid code development it is recommended to keep following the [Changes](http://bycon.progenetix.org/changes/)
page.

### Installation

The installation is documented [`on the website`](http://bycon.progenetix.org/installation/)
(and in the page's Markdown [source here](./docs/installation.md)).

Since version `1.0.55` (2023-06-22) additional "services" may be installed from
the [`byconaut`](https://github.com/progenetix/byconaut/) repository.