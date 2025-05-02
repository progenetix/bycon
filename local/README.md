The files in the `local` directory here are used to supplement package internal
files of the same name, to provide configurations and parameters specific to the
local setup. At the v2.0 version these files are:

#### `authorizations.yaml`

Please see the notes in the installation documentation.

#### `dataset_definitions.yaml`

Information about the datasets served by the one or more beacon instances (see below).

#### `instance_definitions.yaml`

Beacon instance parameters; e.g. a single installation can serve several beacons
with their own domains (independent of the datasets/databases).

#### `env_paths.yaml`

* `server_tmp_dir_loc` which is needed for some temporary files (e.g. BED
  files for UCSC browser integration)
* `bycon_install_dir` which is needed by the `install.py` installer script
* ...