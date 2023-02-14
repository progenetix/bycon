#!/usr/bin/env python3

import cgi, cgitb
import re, json, yaml
from os import path, environ, pardir
import sys, datetime, argparse
from pymongo import MongoClient

pkg_path = path.join( path.dirname( path.abspath(__file__) ), pardir, pardir )
sys.path.append( pkg_path )
from bycon import *

################################################################################
################################################################################
################################################################################

def main():

    collations()
    
################################################################################

def collations():

    initialize_bycon_service(byc)
    select_dataset_ids(byc)
    # first the filter => collation_type which removes the filter if type match
    parse_filters(byc)
    _check_collation_type_query(byc)
    create_empty_service_response(byc) 
    cgi_break_on_errors(byc)

    # data retrieval & response population
    d_k = collations_set_delivery_keys(byc)

    c = byc["service_config"]["collection_name"]

    ##################################

    # this is all just a bit complex since a multi-dataset response is taken care of...
    s_s = { }

    mongo_client = MongoClient( )
    for ds_id in byc[ "dataset_ids" ]:
        mongo_db = mongo_client[ ds_id ]        
        mongo_coll = mongo_db[ c ]
        for collation in mongo_coll.find( byc["queries"], { "_id": 0 } ):

            if "codematches" in byc["method"]:
                if int(collation.get("code_matches", 0)) < 1:
                    continue

            i_d = collation["id"]
            if not i_d in s_s:
                s_s[ i_d ] = { }

            if len(d_k) < 1:
                d_k = list(collation.keys())
            else:
                d_k = [ v for v in d_k if v in list(collation.keys()) ]

            for k in d_k:
                if k in byc["service_config"]["integer_keys"]:
                    # for the multi-ds_id integration
                    if k in s_s[ i_d ]:
                        s_s[ i_d ][ k ] += int(collation[ k ])
                    else:
                        s_s[ i_d ][ k ] = int(collation[ k ])
                elif k == "hierarchy_paths":
                    h_p = []
                    for p in collation[ "hierarchy_paths" ]:
                        p.update({"order": int(p["order"]) })
                        h_p.append(p)
                    s_s[ i_d ][ k ] = h_p
                else:
                    s_s[ i_d ][ k ] = collation[ k ]
            else:
                continue

    mongo_client.close( )

    populate_service_response( byc, list(s_s.values()))
    cgi_print_response( byc, 200 )

################################################################################
################################################################################
################################################################################

def _check_collation_type_query(byc):

    byc["queries"] = {}

    if "id" in byc["form_data"]:
        if re.match(r'^\w[^:]+?:\w.+?$', byc["form_data"]["id"]):
            byc.update({"queries": {"id": byc["form_data"]["id"] } } )
            return byc

    if "filters" in byc:
        # TODO: This hack fixes the translation of filters for collation types
        f_fs = byc["filters"]
        c_t_i = []
        for i, f in enumerate(f_fs):
            if f["id"] in byc["filter_definitions"].keys():
                c_t_i.append(i)

        if len(c_t_i) > 0:
            if not "collation_types" in byc["form_data"]:
                byc["form_data"].update({"collation_types":[]})
            for c in c_t_i:
                byc["form_data"]["collation_types"].append(f_fs[c]["id"])

        byc["filters"] = [f_fs[i] for i, e in enumerate(f_fs) if i not in c_t_i]

    q_l = []
    f_q = False
    if len(byc["filters"]) == 1:
        f_q = byc["filters"][0]
    elif len(byc["filters"]) > 1:
        f_q = {"$or": byc["filters"] }
    if f_q is not False:
        q_l.append(f_q)

    c_q = False
    if "collation_types" in byc["form_data"]:
        fs = byc["form_data"]["collation_types"]
        if len(fs) > 0:
            c_q = { "collation_type": {"$in": byc["form_data"]["collation_types"] } }
    if c_q is not False:
        q_l.append(c_q)

    if len(q_l) == 1:
        byc.update({"queries": q_l[0]})
    elif len(q_l) > 1:
        byc.update({"queries": {"$and": q_l } } )

    return byc

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
