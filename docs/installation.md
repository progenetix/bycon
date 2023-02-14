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
contained n `/services`.

###  `bycon` library install

In February 2023 `bycon` has been mad available as a Pypi package with standard
installation through `pip install bycon`.

### Beacon server installation

The project root contains an `install.py` script to distribute the server scripts
into the webserver root. Necessary parameters have to be adjusted in the accompagnying
`install.yaml`.

!!! warning "Configuration adjustments"
    
    Many of the parameters in `bycon` are pre-defined in `bycon/config/....yaml`
    files which are installed into the `bycon` package in your Python `site-packages`
    tree. These configurations can be overwritten by providing modified copies
    in `your_script_directory/local/`. 

### Local complete stack installation 

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

!!! note "Script dependencies"
    
    Many functions in `bycon` require the existence of local configuration files
    (e.g. for dataset definitions) in a `local` directory in the path of your
    calling scripts or CGIs.



