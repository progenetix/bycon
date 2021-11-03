#!/usr/local/bin/python3

import cgi, cgitb
import re, json
from os import environ, path, pardir
import sys

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from beaconServer.lib.read_specs import read_local_prefs
from beaconServer.lib.cgi_utils import rest_path_value, cgi_print_rewrite_response

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

    ids()
    
################################################################################

def ids():

    byc = {}

    read_local_prefs( "ids", dir_path, byc )

    id_in = rest_path_value("ids")

    if id_in:
        for f_p in byc["this_config"]["format_patterns"]:
            pat = re.compile( f_p["pattern"] )
            link = f_p["link"]
            if pat.match(id_in):
                lid, pre, sep, code = pat.match(id_in).group(2, 3, 4, 5)
                if "_" in sep:
                    lid = "{}:{}".format(pre, code)
                cgi_print_rewrite_response(link, lid)

    print('Content-Type: text')
    print('status:422')
    print()
    print("No correct id provided. Please refer to the documentation at http://info.progenetix.org/tags/services/")
    exit()

################################################################################
################################################################################

if __name__ == '__main__':
    main()
