# BeaconPlus - Beacon Front-end for Genomic Data Queries

![Beacon Icon](https://docs.progenetix.org/img/logo_beacon.png){ align=right width=25px} As part of the Beacon project, since early 2016 the [Theoretical Cytogenetics and Oncogenomics Group](https://baudisgroup.org) at the University of Zurich develops the
[Beacon<sup><span style="color: #d00;">+</span></sup> demonstrator](https://beaconplus.progenetix.org/),
to show current functionality and test future Beacon protocol extensions.

The Beacon<sup><span style="color: #d00;">+</span></sup> implementation is a
custom front end on top of the [`bycon`](http://bycon.progenetix.org)
code with emphasis on structural genome variations from cancer samples.

An extended implementation of the Beacon<sup><span style="color: #d00;">+</span></sup> code is provided through the [Progenetix](https://progenetix.org) project.

!!! note "More Documentation"

    The documentation relevant to the API can be found in these locations:

    * [`bycon` package documentation](http://bycon.progenetix.org)
    * Beacon v2 [documentation site](http://docs.genomebeacons.org)

## Installation

The project code for the BeaconPlus front end lives inside `bycon/beaconplusWeb`
and is tested as a static compiled React project (YMMV ...).

### Configuration

Please edit the target installation directory `server_site_dir_loc` in the
`local/local_paths.yaml` configuration file.

Adjustments to dataset definitions etc. being used by the front end are in
`bycon/beaconplusWeb/src/config.js`.

Additionally runtime variables for server name etc. should be set in the environmental
definitions in `bycon/beaconplusWeb/env`.

### Compile & Install

The developer runner `updev.sh` also calls the `install.py` script which asks
for installation of the front end. It boils down to

```bash
cd bycon/beaconplusWeb
npm run local
```
... for local test installations or 

```bash
cd bycon/beaconplusWeb
npm run update
```
... for the outside facing server one (YMMV; these just invoke different settings
defined in `bycon/beaconplusWeb/env`).