# Welcome to the `bycon` project documentation

## Bycon - a Python-based environment for the Beacon v2 genomics API

The `bycon` project - at least at its current stage - is a mix of _Progenetix_ (i.e. GA4GH object model derived, _MongoDB_ implemented) - data management, and the implementation of middleware & server for the Beacon API.

!!! info "Bycon Code"

    The `bycon` code is maintained in the [`progenetix/bycon` repository](http://github.com/progenetix/bycon/). Utility scripts & functions reside in the [`byconaut`](http://github.com/progenetix/byconaut/) and (this one is really "scripty") [`byconeer`](http://github.com/progenetix/byconeer/) repositories but are so far not (well) documented & may contain deprecated or "internal use" code.

More information about the original use _Progenetix_ case can be found [on the project's documentation site](https://docs.progenetix.org/).

### `bycon` Directory Structure

#### `beaconServer`

* web applications for data access
* Python modules for Beacon query and response functions in `lib`

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
  |- bycon
  |   |
  |   |- beaconServer
  |   |   |
  |   |   |- beacon.py
  |   |   |- datasets.py
  |   |   |- configuration.py
  |   |   |- entryTypes.py
  |   |   |- filteringTerms.py
  |   |   `- ... .py
  |   |
  |   |- config
  |   |   |
  |   |   |- beacon_mappings.yaml
  |   |   |- config.yaml
  |   |   |- dataset_definitions.yaml
  |   |   |- filter_definitions.yaml
  |   |   `- ..._definitions.yaml
  |   |
  |   |- lib
  |   |   |
  |   |   |- cgi_parsing.py
  |   |   |- read_specs.py
  |   |   |- parse_filters_request.py
  |   |   |- query_generation.py
  |   |   |- query_execution.py
  |   |    `- ...
  |   |
  |   |- rsrc
  |   |   `- ...
  |   |
  |   `- schemas
  |       `- ...
  |
  |- docs
  |    `- ... documentation website source files ...
  |
  |- local
  |   |
  |   |- beacon_defaults.yaml
  |   |- dataset_definitions.yaml
  |   `- local_paths.yaml
  |
  |- install.py
  |- install.yaml
  `- `requirements.txt` and other Python packaging files
...
```

## External `services`

The _bycon_ environment - together with the [Progenetix](http://progenetix.org)
resource - provide a growing numer of data services in (cancer) genomics and
disease ontologies. Since `bycon` 1.0.55 (2023-06-22) `/services` resides in the
[`byconaut`](http://github.com/progenetix/byconaut/) repository.
