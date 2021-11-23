[![License: CC0-1.0](https://img.shields.io/badge/License-CC0%201.0-lightgrey.svg)](http://creativecommons.org/publicdomain/zero/1.0/)

## Bycon - a Python-based environment for the Beacon v2 genomics API

The `bycon` project - at least at its current stage - is a mix of _Progenetix_ (i.e. GA4GH object model derived, _MongoDB_ implemented) - data management, and the implementation of middleware & server for the Beacon API.

More information about the current status of the package can be found in the inline
documentation which is also [presented in an accessible format](https://info.progenetix.org/tags/Beacon.html) on the _Progenetix_ website.

### More Documentation

#### [Services](./services/doc/services.md)

The _bycon_ environment - together with the [Progenetix](http://progenetix.org)
resource - provide a growing numer of data services in (cancer) genomics and
disease ontologies. _bycon_'s services are tools to enable the APIs.

### Directory Structure

##### `beaconServer`

* web applications for data access
* Python modules for Beacon query and response functions in `lib`

##### `services`

* web applications and libraries extending the `bycon` environment

##### `byconeer`

* locally run applications and utilities for (Progenetix) data import, access & processing
* data management in the [MongoDB](http://mongodb.org) based _Progenetix_ database environment

#### Internal structure

```
bycon
  |
  |- config
  |    |- beacon_mappings.yaml
  |    |- config.yaml
  |    |- dataset_definitions.yaml
  |    |- filter_definitions.yaml
  |    |- ..._definitions.yaml
  |
  |- beaconServer
  |    |- datasets.py
  |    |- biosamples.py
  |    |- filteringTerms.py
  |    |- variants.py
  |    |- ... .py
  |    |
  |    |    |- config
  |    |    |- schemas
  |    |    |   |- beacon.yaml
  |    |    |   |- ... .yaml
  |    |    |
  |    |    |- biosamples.yaml
  |    |    |- ... .yaml
  |    |
  |    |- doc
  |    |    |- bycon.md
  |    |    |- handovers.md
  |    |    |- ... .md
  |    |
  |    |- lib
  |    |    |- cgi_parse.py
  |    |    |- read_specs.py
  |    |    |- parse_filters.py
  |    |    |- query_generation.py
  |    |    |- query_execution.py
  |    |
  |    |- rsrc
  |         |- ...
  |
  |- services
  |    |- config
...
```

##### `config`

* top-level, general configurations
* in `beaconServer`, `services` ... specific configuration files for the
individual endpoints
  - these specify e.g. which configurations are loaded or response content
* YAML ...

##### `doc`

* documentation, in Markdown

##### `lib`

* Python libraries

##### `rsrc`

* various resources beyond configuration data
    - mapping input table(s)
    - external schema dumps
    - ...


