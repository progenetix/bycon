#!/usr/local/bin/python3

import cgi, cgitb
import re, json, yaml
from os import path, environ, pardir
import sys, datetime, argparse
from pymongo import MongoClient

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer.lib.cgi_parse import *
from beaconServer.lib.parse_filters import *
from beaconServer.lib.service_utils import *

################################################################################
################################################################################
################################################################################

def main():

    collations()
    
################################################################################

def collations():

    byc = initialize_service()

    select_dataset_ids(byc)
    parse_filters(byc)
    create_empty_service_response(byc) 
    cgi_break_on_errors(byc)

    # data retrieval & response population
    d_k = collations_set_delivery_keys(byc)

    c = byc["this_config"]["collection_name"]

    # TODO: move the query generation...
    f_q = False
    try:
        if len(byc["form_data"]["filters"]) == 1:
            f_q = {"id": byc["form_data"]["filters"][0] }
        elif len(byc["form_data"]["filters"]) > 1:
            f_q = {"$or": byc["form_data"]["filters"] }
    except:
        pass

    c_t_q = _get_collation_type_request(byc)
    q_l = []
    if c_t_q is not False:
        q_l.append(c_t_q)
    if f_q is not False:
        q_l.append(f_q)

    query = {}
    if len(q_l) == 1:
        query = q_l[0]
    elif len(q_l) > 1:
        query = {"$and": q_l }

    ##################################

    s_s = { }

    mongo_client = MongoClient( )
    for ds_id in byc[ "dataset_ids" ]:
        mongo_db = mongo_client[ ds_id ]        
        mongo_coll = mongo_db[ c ]
        for subset in mongo_coll.find( query ):

            if "codematches" in byc["method"]:
                if not "code_matches" in subset:
                    continue
                if int(subset[ "code_matches" ]) < 1:
                    continue

            i_d = subset["id"]
            if not i_d in s_s:
                s_s[ i_d ] = { }
            for k in d_k:
                if k in subset.keys():
                    if k in byc["this_config"]["integer_keys"]:
                        if k in s_s[ i_d ]:
                            s_s[ i_d ][ k ] += int(subset[ k ])
                        else:
                            s_s[ i_d ][ k ] = int(subset[ k ])
                    elif k == "hierarchy_paths":
                        h_p = []
                        for p in subset[ k ]:
                            if "order" in p:
                               p.update({"order": int(p["order"]) })
                            h_p.append(p)
                        s_s[ i_d ][ k ] = h_p
                    else:
                        s_s[ i_d ][ k ] = subset[ k ]
                else:
                    continue

    mongo_client.close( )

    populate_service_response( byc, _response_map_results( list(s_s.values()), byc))
    cgi_print_response( byc, 200 )

################################################################################
################################################################################
################################################################################

def _get_collation_type_request(byc):

    if "form_data" in byc:
        # TODO: This hack fixes the translation of filters for collation types
        if "filters" in byc["form_data"]:
            for f in byc["form_data"]["filters"]:
                if re.match(r'^\w+?$', f):
                    if not "collationTypes" in byc["form_data"]:
                        byc["form_data"].update({"collationTypes":[]})
                    byc["form_data"]["collationTypes"].append(f)
        byc["form_data"].update({"filters": []})
        if "collationTypes" in byc["form_data"]:
            fs = byc["form_data"]["collationTypes"]
            if len(fs) > 0:
                return { "collation_type": {"$in": byc["form_data"]["collationTypes"] } }

    return False

################################################################################

def _response_map_results(data, byc):

    # the method keys can be overriden with "deliveryKeys"
    d_k = collations_set_delivery_keys(byc)

    if len(d_k) < 1:
        return data

    results = [ ]

    for res in data:
        s = { }
        for k in d_k:
            # TODO: cleanup and add types in config ...
            if "." in k:
                k1, k2 = k.split('.')
                if k1 in res.keys():
                    if k2 in res[ k1 ]:
                        s[ k ] = res[ k1 ][ k2 ]
            elif k in res.keys():
                if "start" in k or "end" in k:
                    s[ k ] = int(res[ k ])
                else:
                    s[ k ] = res[ k ]
        results.append( s )

    return results

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
