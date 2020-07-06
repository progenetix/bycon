#!/usr/local/bin/python3

from os import environ as environ
from os import path as path
from sys import path as sys_path
import re
import cgitb
from urllib.parse import urlparse

# local
dir_path = path.dirname(path.abspath(__file__))
sys_path.append(path.join(path.abspath(dir_path), '..'))

from bin.cytomapper import cytomapper
from bin.byconplus import byconplus
from bin.collations import collations

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

Also, key=value parameters can be provided as path elements:

* <https://progenetix.org/services/cytomapper/assemblyId=ncbi36.1/cytoBands=8q/text=1>


podmd"""

################################################################################
################################################################################
################################################################################

def main():

    url_comps = urlparse( environ.get('REQUEST_URI') )

    if "debug" in environ.get('REQUEST_URI'):
        cgitb.enable()
        print('Content-Type: text')
        print()

    i = 0
    p_items = re.split(r'\/|\&', url_comps.path)
    for p in p_items:
        i += 1
        if p == "services":
            f = p_items[ i ]

    if f == "cytomapper":
        cytomapper()
    elif f == "byconplus":
        byconplus()
    elif f == "collations":
        collations()

################################################################################
################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
