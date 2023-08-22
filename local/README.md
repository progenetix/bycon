The files in the `local` directory here are used to supplement package internal
files of the same name, to provide configurations and parameters specific to the
local setup. At the v1.1 version stage these files are:

#### `beacon_defaults.yaml`

* `defaults` - e.g. the required name of a default dataset
* `entity_defaults` - can be empty or contain entry type definitions beyond the
  standard entry types (e.g. `biosample` or `genomicVariant`)
* mappings between e.g. path elements and the respective entry types beyond the 
  standard ones (e.g. `g_variants` -> `genomicVariant`) 

#### `dataset_definitions.yaml`

* definitions for the local instance's datasets
* we now include reference to a standard `examplez` dataset in the package internal
  definitions which can be installed through `byconaut`

#### `local_paths.yaml`

* e.g. `server_tmp_dir_loc` which is needed for some temporary files (e.g. BED
  files for UCSC browser integration)