#!/usr/bin/env python3
import re
from os import environ, path, pardir

from bycon import *

services_conf_path = path.join( path.dirname( path.abspath(__file__) ), "config" )
services_lib_path = path.join( path.dirname( path.abspath(__file__) ), "lib" )
sys.path.append( services_lib_path )
from service_helpers import read_service_prefs

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
    try:
        ids()
    except Exception:
        print_text_response(traceback.format_exc(), 302)
    
################################################################################

def ids():
    set_debug_state(debug=0)
    read_service_prefs( "ids", services_conf_path)
    id_in = rest_path_value("ids")
    output = rest_path_value(id_in)
    s_c = BYC.get("service_config", {})
    f_p_s = s_c.get("format_patterns", {})

    if id_in:
        for f_p in f_p_s:
            pat = re.compile( f_p["pattern"] )
            if pat.match(id_in):
                lid = id_in  
                link = f_p["link"]
                pim = f_p.get("prepend_if_missing", "")
                if len(pim) > 0:
                    if pim in lid:
                        pass
                    else:
                        lid = pim+lid
                print_uri_rewrite_response(link, lid)

    print('Content-Type: text')
    print('status:422')
    print()
    print("No correct id provided. Please refer to the documentation at http://info.progenetix.org/tags/services/")
    exit()


################################################################################
################################################################################

if __name__ == '__main__':
    main()
