#!/usr/local/bin/python3

import cgi, cgitb
import re, json
import sys, os
from urllib.parse import urlparse

# local
dir_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(os.path.abspath(dir_path), '..'))
from bycon.read_specs import *

"""podmd
The `ids` service forwards compatible, prefixed ids (see `config/ids.yaml`) to specific
website endpoints. There is no check if the id exists; this is left to the web
page handling itself.

Stacking with the "pgx:" prefix is allowed.
* <https://progenetix.org/services/ids/pgxbs-kftva5zv>
* <https://progenetix.org/services/ids/PMID:28966033>
* <https://progenetix.org/services/ids/NCIT:C3262>
podmd"""

################################################################################
################################################################################
################################################################################

def main():

    ids("ids")
    
################################################################################

def ids(service):

    # config = read_bycon_config( os.path.abspath( dir_path ) )
    these_prefs = read_named_prefs( service, dir_path )

    url_comps = urlparse( environ.get('REQUEST_URI') )
    p_items = re.split(r'\/|\&', url_comps.path)
    i = 0
    id_in = ""

    for p in p_items:
        i += 1
        if len(p_items) > i:
            if p == "ids":
                id_in = p_items[ i ]
                break

    for f_p in these_prefs["format_patterns"]:
        pat = re.compile( f_p["pattern"] )
        link = f_p["link"]
        if pat.match(id_in):
            lid = pat.match(id_in).group(2)
            print("Status: 302")
            print("Location: {}{}".format(link, lid))
            print()
            exit()

    print('Content-Type: text')
    print('status:422')
    print()
    print("No correct id provided. Please refer to the documentation at http://info.progenetix.org/tags/services/")
    exit()

################################################################################
################################################################################

if __name__ == '__main__':
    main()
