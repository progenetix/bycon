# Welcome to the `bycon` project documentation

## Bycon - a Python-based environment for the Beacon v2 genomics API

The `bycon` project - at least at its current stage - is a mix of _Progenetix_ (i.e. GA4GH object model derived, _MongoDB_ implemented) - data management, and the implementation of middleware & server for the Beacon API.

!!! info "Bycon Code"

    The `bycon` code is maintained in the [`progenetix/bycon` repository](http://github.com/progenetix/bycon/). Utility scripts & functions reside in the [`byconeer`](http://github.com/progenetix/byconeer/) and [`byconaut`](http://github.com/progenetix/byconaut/) repositories but are so far not documented & may contain deprecated or "internal use" code.

More information about the current status of the package can be found in the inline
documentation which is also [presented in an accessible format](https://info.progenetix.org/tags/Beacon.html) on the _Progenetix_ website.

### `bycon` Directory Structure

#### `beaconServer`

* web applications for data access
* Python modules for Beacon query and response functions in `lib`

#### `services`

The _bycon_ environment - together with the [Progenetix](http://progenetix.org)
resource - provide a growing numer of data services in (cancer) genomics and
disease ontologies. _bycon_'s services are tools to enable the APIs.

* web applications and libraries extending the `bycon` environment

#### `config`

* top-level, general configurations
* in `beaconServer`, `services` ... specific configuration files for the
individual endpoints
  - these specify e.g. which configurations are loaded or response content
* YAML ...

#### `docs`

* documentation, in Markdown, as source for documentation builded with `mkdocs`

#### `lib`

* Python libraries

#### `rsrc`

* various resources beyond configuration data
    - mapping input table(s)
    - external schema dumps
    - ...




#### Overview

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
  |- docs
  |    `- ... documentation website source files ...
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
  |    |    |- cgi_parsing.py
  |    |    |- read_specs.py
  |    |    |- filter_parsing.py
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
