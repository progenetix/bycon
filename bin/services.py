#!/usr/local/bin/python3

from os import environ as environ
from os import path as path
from urllib.parse import urlparse
import sys, re, cgitb

from importlib import import_module

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))

# from bin.biosamples import biosamples
# from bin.byconplus import byconplus
# from bin.collations import collations
# from bin.cytomapper import cytomapper
# from bin.dbstats import dbstats
# from bin.deliveries import deliveries
# from bin.genespans import genespans
# from bin.geolocations import geolocations
# from bin.ids import ids
# from bin.ontologymaps import ontologymaps
# from bin.phenopackets import phenopackets
# from bin.publications import publications

"""podmd
The `services` application deparses a request URI and calls the respective
script. The functionality is combined with the correct configuration of a 
rewrite in the server configuration:

```
RewriteRule     "^/services(.*)"     /cgi-bin/bycon/bin/services.py$1      [PT]
```

This allows the creattion of canonical URLs, e.g.:

* <https://progenetix.org/services/byconplus/?datasetIds=arraymap,progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=9&variantType=DEL&start=18000000&start=21975097&end=21967753&end=26000000&filters=icdom-94403>
* <https://progenetix.org/services/cytomapper/?assemblyId=ncbi36.1&cytoBands=8q&text=1>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    services = [
        "biosamples",
        "byconplus",
        "cytomapper",
        "dbstats",
        "deliveries",
        "geolocations",
        "ids",
        "publications",
        "genespans",
        "ontologymaps",
        "phenopackets",
        "collations"
    ]

    if "debug=1" in environ.get('REQUEST_URI'):
        cgitb.enable()
        print('Content-Type: text')
        print()

    url_comps = urlparse( environ.get('REQUEST_URI') )
    p_items = re.split(r'\/|\&', url_comps.path)
    i = 0
    f = ""

    for p in p_items:
        if len(p_items) > i:
            i += 1
            if p == "services":
                if p_items[ i ] in services:    
                    f = p_items[ i ]
                    
                    # dynamic package/function loading
                    try:
                        mod = import_module(f)
                        serv = getattr(mod, f)
                        serv(f)
                    except Exception as e:
                        print('Service name error: {}'.format(e))

                    exit()

    print('Content-Type: text')
    print('status:422')
    print()
    print("No correct service path provided. Please refer to the documentation at http://info.progenetix.org/tags/services/")
    exit()

################################################################################
################################################################################

if __name__ == '__main__':
    main()
