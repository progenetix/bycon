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

### `docs`

* documentation, in Markdown, as source for documentation builded with `mkdocs`

### `lib`

* Python libraries

### `rsrc`

* various resources beyond configuration data
    - mapping input table(s) for ontology trees
    - ...

### `importers` and `housekeepers`

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
  |   |   |- cgi_parsing.py
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
  |   `- local_paths.yaml
  |   `- local_paths.yaml
  |- install.py
  `- `requirements.txt` and other Python packaging files
...
```


##  `bycon` library install (not recommended)

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
    * we use a rewrite directive to the main beacon (& optional services) apps which
      handle then path deparsing and calling of individual apps:
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

    RewriteRule     "^/?services/(.*)"     /cgi-bin/bycon/services/services.py/$1      [PT]
    RewriteRule     "^/?beacon/(.*)"     /cgi-bin/bycon/beaconServer/beacon.py/$1      [PT]
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
into the webserver root. Necessary parameters have to be adjusted in the accompagnying
`install.yaml`.

!!! warning "Configuration adjustments"
    
    Many of the parameters in `bycon` are pre-defined in `bycon/config.py`
    file and the `bycon/definitions/....yaml` files which are installed into the
    `bycon` package in your Python `site-packages` tree. Additional configurations
    can be provided through files in `local/....yaml` and are the copied during
    installation into `your_script_directory/local/`.

### Some configurations

#### Preamble & Imports

The scripts in `beaconServer` and `byconServices` are configured as exacutables using
the system Python `#!/usr/bin/env python3`.

#### `local/authorizations.yaml` (**experimental**)

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

#### `local/local_paths.yaml`

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

#### `local/dataset_definitions.yaml`

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

==TBD==

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

### Importing data `importers`

==TBD==

### Maintaining, pre-processing or deleting data `housekeepers`

==TBD==

## Testing

The following tests are based on the existence of the `examplez` database.

### Command line test

Those tests can be run either from the local `bycon/bycon/beaconServer/` directory
or from the corresponding one in the web cgi directory, if installed.

```
./info.py
./beacon.py --output json -d examplez
./beacon.py --output json -d examplez --testMode true
./beacon.py --output json -d examplez --testMode true --requestEntityPathId biosamples
./beacon.py --output json -d examplez --testMode true --requestEntityPathId biosamples --testModeCount 1
./beacon.py --output json -d examplez --testMode true --requestEntityPathId g_variants
./beacon.py --output json -d examplez --testMode true --requestEntityPathId individuals
./beacon.py --output json -d examplez --filters "UBERON:0000310"
./beacon.py --output json -d examplez --filters "pgx:TCGA-BRCA"
```


