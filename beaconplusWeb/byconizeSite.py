#!/usr/local/bin/python3

import inspect, sys, re, yaml
from os import getlogin, makedirs, path, system
from pathlib import Path
from collections import OrderedDict

dir_path = path.dirname( path.abspath(__file__) )

from bycon import *

################################################################################

def main():
    """
    This script is intended to harmonize parameters between the local bycon
    installation and the front end. Just started...
    """
    site_path = path.join(dir_path, "src")
    # TODO: Uses a yaml duplicate of the `config.js` file since I need to look up
    # how to read in parameters from .js into Python ...
    ds_default = "___none___"
    sp_conf_file = path.join(site_path, "site-specific", "config.js")
    with open(sp_conf_file) as spf:
        for line in spf:
            if "default_dataset_id" in line:
                ds_default = re.search(r"default_dataset_id['\"]\s*:\s*['\"]([^'\"]+)['\"]", line).group(1)
                break

    print(f'Using default dataset ID: {ds_default}')

    bp_formpar_file = path.join(site_path, "config", "beaconSearchParameters.yaml")
    with open(bp_formpar_file) as bpf:
        bp_formpars = yaml.load(bpf, Loader=yaml.FullLoader)

    dataset_opts = dataset_options(ds_default)
    bp_formpars["parameters"]["datasetIds"].update({"options": dataset_opts})
    with open(bp_formpar_file, 'w') as bpf:
        yaml.dump(bp_formpars, bpf)

    # prjsonnice(bp_formpars["parameters"]["datasetIds"]["options"])


################################################################################

def dataset_options(ds_default):
    # TODO: Order? Here now using 
    dso = []
    for ds, dsd in BYC.get("dataset_definitions", {}).items():
        if ds == ds_default:
            dso.append({
                "value": ds,
                "label": f'{dsd.get("name", "")} ({ds})'
            })
    for ds, dsd in BYC.get("dataset_definitions", {}).items():
        if ds != ds_default:
            dso.append({
                "value": ds,
                "label": f'{dsd.get("name", "")} ({ds})'
            })
    return dso


################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
