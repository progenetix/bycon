---
title: Installation
---

## Project Structure

The `bycon` project contains libraries (`/lib`), global configuration files
(`/config`), resource files (`/rsrc`) and data scheams (`/schemas`). All these
are distributed as part of the `bycon` package.

!!! warning "Highly Experimental"
    
    At this time the `bycon` configuration files are _very_ specific for
    the Progenetix use case. While in principle one can use the current code base
    to create a complete Beacon v2 setup this requires quite a bit of customization.

Additionally to the library and associated files a complete `bycon`-base Beacon
server setup requires the installation of various endpoint apps contained in
`/beaconServer`. Progenetix also makes use of many server apps (e.g. for retrieving
supporting data such as collation statistics or genomic parameters) which are
contained n `/services`

###  `bycon` library install

In February 2023 `bycon` has been mad available as a Pypi package with standard
installation through `pip install bycon`.

### Beacon server installation

The project root contains an `install.py` script to distribute the server scripts
into the webserver root. Necessary parameters have to be adjusted in the accompagnying `install.yaml`.

!!! warning "Incompatibility of PyPi & server installs"
    
    The current setup has many parameters necessary for the webserver which need
    to be adjusted in the global config files. However, if one makes use of the
    PyPi install the current (Progenetix specific) defaults there will be used.
    Therefore, a complete `bycon` setup right now requires the removal of the
    `bycon` package and local installation of a modified distribution.

#### Local complete stack installation 

The local developer mode installation removes the system `bycon`, compiles the
current code base (e.g. containing your modifications) and then runs the installer
script for the distribution of the server scripts. The following utility code
is provided with the `updev.sh` script (may change over time...):

```bash
pip3 uninstall bycon
rm -rf ./dist
python3 -m build --sdist .
BY=(./dist/*tar.gz)
pip3 install $BY
./install.py
```


