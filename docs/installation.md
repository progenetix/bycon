# Installation

## Project Structure

The `bycon` project contains source code for the eponymous Python package
as well as a number of server applications which are used to provide a Beacon 
webserver, additional server functions for statistical and graphical readouts
(specifically geared towards copy number variation data) as well as support 
applications and libraries for data I/O and management of the implied MongoDB
database environment. 

!!! warning "Experimental Libraries"

    At this time (**bycon v2.0 "Taito City"**) the project's
    libraries - which in principle can be installed directly from the Python Package
    Index - should *not* be used for external applications since libary structure
    and dependencies might change and are only kept in sync within the wider project
    itself.

Additionally to the library and associated files a complete `bycon`-base Beacon
server setup requires the installation of various endpoint apps contained in
`/beaconServer` and - optionally -  `/byconServices` (e.g. for retrieving
supporting data such as collation statistics or genomic parameters).

We also provide a number of utility scripts and libraries which are not part of the
general installation and might contain deprecated code or dependencies through the
[`byconaut`](https://github.com/progenetix/byconaut/) project.


### `./beaconServer`

* web applications for data access
* Python modules for Beacon query and response functions in `lib`

### `./bycon`

* Python libraries for data handling and Beacon API functions with a main
  `beacon.py` application calling the server functions and libraries as well as
  configuration data contained in subdirectories and files:
    - `./bycon/byconServiceLibs` for beyond Beacon functionality executed through
      the endpoints in `byconServices`
    - `./bycon/config` for instance independent or default configuration files
    - `./bycon/lib` for the Python libraries (_i.e._ the real code)
    - `./bycon/rsrc` with support files (ATM the genome and cytoband mappings)
    - `./bycon/schemas` contains Beacon and other schema files, both in YAML 
      source and JSON compiled format (JSON is read by the scripts)

### `./docs`

* documentation, in Markdown, as source for documentation builded with `mkdocs`


### `./rsrc`

* various resources beyond configuration data
    - mapping input table(s) for ontology trees
    - ...

### `./importers` and `./housekeepers`

* Python scripts for data import and maintenance; see below

### Overview

```
bycon
  |
  |- beaconServer
  |   |
  |   `- beacon.py
  |- bycon
  |   |
  |   |- config
  |   |   |
  |   |   |- beacon_mappings.yaml
  |   |   |- dataset_definitions.yaml
  |   |   |- filter_definitions.yaml
  |   |   `- ..._definitions.yaml
  |   |- lib
  |   |   |
  |   |   |- parameter_parsing.py
  |   |   |- read_specs.py
  |   |   |- query_generation.py
  |   |   |- query_execution.py
  |   |    `- ...
  |   |- byconServiceLibs
  |   |   |
  |   |   |- bycon_plot.py
  |   |    `- ...
  |   `- rsrc
  |        `- ...
  |- docs
  |    `- ... documentation website source files ...
  |- local
  |   |- beacon_defaults.yaml
  |   |- dataset_definitions.yaml
  |   |- instance_definitions.yaml
  |   `- local_paths.yaml
  |   
  |- install.py
  `- `requirements.txt` and other Python packaging files
...
```

??? note "PyPi based `bycon` library installation (not recommended)""

    Since February 2023 `bycon` has been mad available as a Pypi package with standard
    installation through `pip3 install bycon`. However, this installation will lack
    the server components and is by itself only suitable for library utilization. 
    In contrast to the package manager based library installations we highly recommend
    to install locally from the source, using the installer provided with the project. 
    Please follow the *Beacon Server Installation* procedure below.

## Beacon Server Installation

### Requirements

An installation of a Beacon environment may involve following repositories and
external requirements:

* [`bycon`](https://github.com/progenetix/bycon/)
    - this repository
    - the core Beacon code for libraries and server API
    - required
* a [MongoDB](https://www.mongodb.com/) database instance
    - see below
    - required
* a webserver setup
    - see below
    - required for full functionality but tests can be run by custom scripts or
      local calls (YMMV)
* [`beaconplus-web`](https://github.com/progenetix/beaconplus-web/)
    - the web front-end (React based with static compilation)
    - represents an advanced Beacon query interface 
    - optional

#### MongoDB database instance

The MongoDB host server can be set with the environmental variable `BYCON_MONGO_HOST`.
It otherwise defaults to `localhost`.

##### Installation

We use a [Homebrew](https://brew.sh) based installation, as detailed on the
[MongoDB website](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-os-x/).
On OS X this boils down to (assuming [Homebrew](https://brew.sh) has been installed):

```sh
brew tap mongodb/brew
brew install mongodb-community
```

Then this shoul dbe started as a service & (probably) needs a restart of the computer
(in case another or version was running etc.).

```sh
brew services start mongodb-community
```

The update works similarly:

```sh
brew tap mongodb/brew
brew upgrade mongodb-community
brew services restart mongodb/brew/mongodb-community
```

#### Webserver Setup

We use a "classical" webserver setup with Apache but probably other options would
be fine...

Some configuration:

- a directory for executables (e.g. .../cgi-bin/) 
    * this has to be set as the default executable (CGI) directory
    * our Mac OS use: `/Library/WebServer/cgi-bin/`
    * we also use a `/bycon` wrapper directory inside the CGI dir (for hosting the
      `beaconServer` and optionally `services` directories with their `....py`
      scripts)
    * **we use a rewrite directive to the main beacon** (& optional services) apps which
      handle then path deparsing and calling of individual apps (see box below)
- a server-writable temporary directory
    * our use: `/Library/WebServer/Documents/tmp/` 

??? info "Example `httpd.conf` configuration settings"

    These are some example configuration settings. Please search for the corresponding
    settings in your server configuration and adjust acordingly.

    ```
    # Set the document root - here using our example, YMMV

    DocumentRoot    /Library/WebServer/Documents
    ```


    ```
    # Enable script execution

    LoadModule cgi_module /usr/libexec/apache2/mod_cgi.so

    # Configure the global CGI-BIN

    ScriptAlias  /cgi      /Library/WebServer/cgi-bin
    ScriptAlias  /cgi-bin  /Library/WebServer/cgi-bin

    <Directory "/Library/WebServer/cgi-bin">
        AllowOverride None
        Options +ExecCGI -MultiViews +SymLinksIfOwnerMatch
        SetHandler cgi-script
        Require all granted
    </Directory>
    ```
    ```
    # Allow (some) CGI-BIN scripts to be called with a short alias.

    RewriteEngine On

    RewriteRule "^/beacon/(.*)"   /cgi-bin/bycon/beaconServer/beacon.py/$1 [PT]
    RewriteRule "^/services/(.*)" /cgi-bin/bycon/services/services.py/$1   [PT]
    RewriteRule "^/?services$"    /cgi-bin/bycon/services/services.py      [PT]
    RewriteRule "^/?beacon$"      /cgi-bin/bycon/beaconServer/beacon.py    [PT]
    ```

    ```
    # Configure the global tmp

    Alias  /tmp      /Library/WebServer/Documents/tmp

    <Directory /Library/WebServer/Documents/tmp>
        Options Indexes FollowSymlinks
        AllowOverride All
        Require all granted
    </Directory>
    ```


### Installation Procedure

The project root contains an `install.py` script to distribute the server scripts
into the webserver root. Necessary parameters such as local paths
have to be adjusted in the configuration files in `local/`, such as in `local_paths.yaml`.

!!! warning "Configuration adjustments"
    
    Many of the parameters in `bycon` are pre-defined in `bycon/config.py`
    file and the `bycon/definitions/....yaml` files which are installed into the
    `bycon` package in your Python `site-packages` tree. Additional configurations
    can be provided through files in `local/....yaml` and are the copied during
    installation into `your_script_directory/local/`.

!!! warning "Recommended installation"

    The preferred method is to modify your local configuration and then perform a local package build, installation
    and server installation by running the `updev.sh` script.  

### Some configurations

#### Preamble & Imports

The scripts in `beaconServer` and `byconServices` are configured as executables using
the system Python `#!/usr/bin/env python3`.

#### `./local/authorizations.yaml` (**experimental**)

While the Progenetix related prjects do not use any authentication
procedures we provide an experimental framework for setting
per dataset access according to a **trusted** user if needed.
This essentially requires access control through a gatekeeper/proxy
service and addition of a registered user with default and dataset specific
permissions corresponding to Beacon `responseGranularity` levels. 

In the example below the beacon will respond with a `count` response
but e.g. grant record level access to a `testuser` but only
for the `examplez` dataset.

```yaml
anonymous:
  default: boolean
mbaudis:
  default: count
  progenetix: record
  cellz: record
  examplez: record
  refcnv: record
testuser:
  examplez: record    
```

#### `./local/local_paths.yaml`

Here at minimum the paths for the webserver `tmp` has to be defined (path elements
as list items):

```
server_tmp_dir_loc:
  - /
  - Library
  - WebServer
  - Documents
  - tmp

server_tmp_dir_web: /tmp
```

#### `./local/dataset_definitions.yaml`

Please modify the data here for your local datasets. The schema should follow
this default, with dataset ids as the root parameters:

```yaml
examplez:
  id: examplez
  name: Progenetix examples
  identifier: 'org.progenetix.examplez'
  description: "selected examples for database test installation"
  createDateTime: 2023-04-01
  updateDateTime: 2023-08-21
  version: 2023-08-21
  externalUrl: "https://bycon.progenetix.org"
  assemblyId: GRCh38
  dataUseConditions:
    duoDataUse:
      - id: DUO:0000004
        label: no restriction
        version: 2023-08-21
```

#### `local/instance_definitions.yaml`

This file defines the different Beacon instances provided through
your installation, e.g. their `info` endpoint's content, URLs
and potentially additional entry types supported.

The file has 2 root parameters for instance definitions:

* **`local`** can be used to override package provided `beacon_defaults` (_i.e._ the `local.beacon.defaults` object is merged with the `config.yaml` provided global `BYC["beacon_defaults"]` object) and `entity_defaults` can modify or add to the ones defined in bycon's `entity_defaults.yaml`
* **domain specific** root parameters allow to modify domains etc. for multi-beacon
  setups, including again entity and beacon defaults per domain/beacon


## Local stack installation 

The local developer mode installation removes the system `bycon`, compiles the
current code base (e.g. containing your modifications) and then runs the installer
script for the distribution of the server scripts. The following utility code
is provided with the `updev.sh` script (may change over time...):

```bash
pip3 uninstall bycon --break-system-packages
rm -rf ./dist
rm ./bycon/beaconServer/local/*.*
python3 -m build --sdist .
BY=(./dist/*tar.gz)
pip3 install $BY --break-system-packages
./install.py
rm -rf ./build
rm -rf ./dist
rm -rf ./bycon.egg-info
```

There is also a `--no-sudo` modification option: `./install.py --no-sudo`

## Loading and maintaining data

The `bycon` project now contains support apps for data
importing and preprocessing; this is evolving...

### Option 1: Direct MongoDB example data import

The project comes with a small example dataset (called `examplez`) which can be imported
directly from the MongoDB database dump. The following command will import the data (adjust the path if necessary):
  
```bash
tar -xzf ./rsrc/mongodump/examplez.tar.gz --directory ./rsrc/mongodump/
mongosh examplez --eval 'db.dropDatabase()'
mongorestore --db examplez ./rsrc/mongodump/examplez/
rm -rf ./rsrc/mongodump/examplez/
```

Additionally you might want to import the services database which
e.g. contains collections for genome positions for genes an geolocations
of most cities (which support specific query types). 

```bash
tar -xzf ./rsrc/mongodump/_byconServicesDB.tar.gz --directory ./rsrc/mongodump/
mongosh _byconServicesDB --eval 'db.dropDatabase()'
mongorestore --db examplez ./rsrc/mongodump/_byconServicesDB/
rm -rf ./rsrc/mongodump/_byconServicesDB/
```

### Option 2: Importing data `importers`

#### Core Data

A basic setup for a Beacon compatible database - as supported by the `bycon` package -
consists of the core data collections mirroring the Beacon default data model:

* `variants`
* `analyses` (which covers parameters from both Beacon `analysis` and `run` entity schemas)
* `biosamples`
* `individuals`

Databases are implemented in an existing MongoDB setup using utility applications by importing data from tab-delimited data files. In principle, only 2 import files are needed for inserting and updating of records:
* a file for the non-variant metadata[^1] with specific header values, where as
  the absolute minimum id values for the different entities have to be provided
* a file for genomic variants, again with specific headers but also containing
  the upstream ids for the corresponding analysis, biosample and individual

The `importers` directory contains scripts supporting data import with a separate [documentation page](./importers/).

### Maintaining, pre-processing or deleting data `housekeepers`

The `housekeepers` directory contains scripts supporting data import with a separate [documentation page](./housekeepers/).

## Testing

The following tests are based on the existence of the `examplez` database.

### Command line test

Those tests can be run either from the local `bycon/bycon/beaconServer/` directory
or from the corresponding one in the web cgi directory, if installed.

```
./beacon.py -d examplez
./beacon.py -d examplez --testMode true
./beacon.py -d examplez --requestEntityPathId biosamples --testMode true
./beacon.py -d examplez --requestEntityPathId biosamples --testMode true --testModeCount 1
./beacon.py -d examplez --requestEntityPathId g_variants --testMode true
./beacon.py -d examplez --requestEntityPathId individuals --testMode true
./beacon.py -d examplez --requestEntityPathId biosamples --filters "pgx:icdom-94003"
```

Of note the `--requestEntityPathId biosamples` etc. here simulates
the corresponding REST path following the `/beacon/` component.

[^1]: Metadata in biomedical genomics is "everything but the sequence variation"

