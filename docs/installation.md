# Installation

## Project Structure

The `bycon` project contains 

* a number of applications to generate a web server exposing a Beacon API
* "beyond Beacon" services functions for file exports and graphical readouts
(with some emphasis on genomic copy number variation data)
* source code for the eponymous Python package
* support applications and libraries for data I/O and management of the database environment
* source code for a React based web front end for the Beacon API
* documentation source files in the form of a Markdown based `mkdocs` project

!!! warning "Experimental Libraries"

    At this time (**bycon v2.5+ "Forked"**) the project
    libraries - which are available through the Python Package
    Index - should *not* be used for external applications since libary structure
    and dependencies might change and are only kept in sync _within_ the project itself.

!!! note "User defined directories"

    The project uses a number of user defined directories for
    configuration files and data. The directories are defined in the
    `local/env_paths.yaml` file and can be modified to your needs.
    The default directories are:

    - essentiall is `local` for configuration files
    - optionally `rsrc` additional classifications and identifiers


### `beaconServer`

* the `beacon.py` web app for all standard Beacon API functions

### `bycon`

* Python libraries for data handling and Beacon API functions as well as
  configuration data contained in subdirectories and files:
    - `bycon/byconServiceLibs` for beyond Beacon functionality executed through
      the endpoints in `byconServices`
    - `bycon/config` for default configuration files
    - `bycon/lib` for the Python libraries (_i.e._ the real code)
    - `bycon/rsrc` with support files (ATM the genome and cytoband mappings)
    - `bycon/schemas` contains Beacon and other schema files, both in YAML 
      source and JSON compiled format (JSON is read by the scripts)

### `docs`

* documentation, in Markdown, as source for documentation builded with `mkdocs`

### `rsrc`

* various resources beyond configuration data
    - mapping input table(s) for ontology trees
    - ...

### `importers` and `housekeepers`

* Python utility applications for data import and maintenance; see below

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
  |
  |- local
  |   |- dataset_definitions.yaml
  |   |- instance_definitions.yaml
  |   `- env_paths.yaml
  |   
  |- install.py
  `- `requirements.txt` and other Python packaging files
...
```

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
* a web front end
    - optional
    - we provide a React based fron end with static compilation inside `bycon/beaconplusWeb`; more extended
    variants from the same stack are e.g. [`progenetix-web`](https://github.com/progenetix/progenetix-web/)
    - represents an advanced Beacon query interface 

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

Then this should be started as a service.

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
be fine. The installation procedure on Mac OS now uses a `brew` based installation
of the Apache webserver.

Some configuration:

- a directory for executables (e.g. .../cgi-bin/) 
    * this has to be set as the default executable (CGI) directory
      - on Mac OS homebrew installation: `/opt/homebrew/var/www/cgi-bin/`
    * we also use a `.../cgi-bin/bycon` wrapper directory for hosting the `beaconServer` and optionally `services` directories with their `....py`
      scripts)
    * **we use a rewrite directive to the main beacon** (& optional services) apps which
      handle then path deparsing and calling of individual apps (see box below)
- a server-writable temporary directory
    * our use: `/opt/homebrew/var/www/Documents/tmp/` 

??? info "Example `httpd.conf` configuration settings"

    These are some example configuration settings. Please search for the corresponding
    settings in your server configuration and adjust acordingly. 

    ```
    # Set the server and document root - here using our example, YMMV

    ServerRoot      /opt/homebrew/opt/httpd

    # Variables section - for modification #########################################

    Define WEBSERVER_ROOT         /opt/homebrew/var/www
    Define APACHE_CONFDIR         /opt/homebrew/etc/httpd
    Define APACHE_LOG_DIR         /opt/homebrew/var/log/httpd
    Define BYCON_WEB_DIR          /cgi-bin/bycon
    Define APACHE_MODULES_DIR     lib/httpd/modules
    Define APACHE_LOCK_DIR        /tmp

    # Variables - derived ##########################################################

    Define DOCUMENT_ROOT          ${WEBSERVER_ROOT}/Documents
    Define SITES_ROOT             ${DOCUMENT_ROOT}/Sites
    Define CGI_BIN_DIR            ${WEBSERVER_ROOT}/cgi-bin
    Define TMP_DIR                ${DOCUMENT_ROOT}/tmp
    Define APACHE_MIME_TYPES_FILE ${APACHE_CONFDIR}/mime.types

    ################################################################################

    DocumentRoot    ${DOCUMENT_ROOT}
    ```

    Script execution:

    ```

    ## CGI-BIN #####################################################################

    LoadModule cgi_module ${APACHE_MODULES_DIR}/mod_cgi.so

    ScriptAlias  /cgi      ${CGI_BIN_DIR}
    ScriptAlias  /cgi-bin  ${CGI_BIN_DIR}

    <Directory "${CGI_BIN_DIR}">
        AllowOverride None
        Options +ExecCGI -MultiViews +SymLinksIfOwnerMatch
        SetHandler cgi-script
        Require all granted
    </Directory>

    ## / CGI-BIN ###################################################################
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
    ## Global tmp ##################################################################

    Alias  /tmp      ${TMP_DIR}

    <Directory "${TMP_DIR}">
        Options Indexes FollowSymlinks
        AllowOverride All
        Require all granted
    </Directory>

    ## / Global tmp ################################################################
    
    ## Add MIME types for serving files ############################################

    <IfModule mime_module>
        TypesConfig ${APACHE_MIME_TYPES_FILE}
        AddType application/x-compress   .Z
        AddType application/x-gzip       .gz .tgz
    </IfModule>

    ## / MIME types ################################################################

    ```


### Local Installation Procedure

The project root contains an `install.py` script to distribute the server scripts
into the webserver root. Necessary parameters such as local paths
have to be adjusted in the configuration files in `local/`, such as in `env_paths.yaml`.

!!! warning "Configuration adjustments"

    Many of the parameters in `bycon` are pre-defined in `bycon/config.py`
    file and the `bycon/config/....yaml` files which are installed into the
    `bycon` package in your Python `site-packages` tree. 
    For your own databases to run additional configurations
    **have to be provided through files in `local/....yaml`**. Those are then added
    during installation to `your_script_directory/local/`. For the server version
    the `local` files have to be copied to this target directory after each modification
    to take effect (happens automatically when running the local installer scripts).

### Some configurations

#### Preamble & Imports

The scripts in `beaconServer` and `byconServices` are configured as executables using
the system Python `#!/usr/local/bin/python3`.

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

#### `./local/env_paths.yaml`

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

#### `local/domain_definitions`

This file defines the different Beacon instances provided through
your installation, e.g. their `info` endpoint's content, URLs
and potentially additional entry types supported.

#### `local/dataset_definitions`




## Local stack installation

The local developer mode installation removes the system `bycon`, compiles the
current code base (e.g. containing your modifications) and then runs the installer
script for the distribution of the server scripts. The following utility code
is provided with the `updev.sh` script (may change over time...):

```bash
pip3 uninstall bycon --break-system-packages
python3 -m build --sdist .
BY=(./dist/*tar.gz)
pip3 install $BY --break-system-packages
./bycon/schemas/bin/yamlerRunner.sh
./markdowner.py
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

## `services.py` and URL Mapping

Bycon web services are called through the `services.py` app which is installed
at the bycon server root. The system path for `services.py` is

```
{bycon_install_dir}/services/services.py
```

... where `bycon_install_dir` has to be user defined inside the `local/env_paths.yaml`
configuration file (see [Installation](installation.md)). The service URL format `progenetix.org/services/__service-name__?parameter=value`
is based on the remapping of the `services.py` script to the `/services` path and
then extraction of the service name as the path parameter following `/services/`.



[^1]: Metadata in biomedical genomics is "everything but the sequence variation"

