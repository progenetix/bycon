#!/usr/local/bin/python3

import re, json, yaml
from os import path, environ, pardir
import sys, datetime
from isodate import date_isoformat
from pymongo import MongoClient
import argparse
from progress.bar import Bar

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from bycon.lib.read_specs import *
"""

## `ontologymapsCreator`

"""

################################################################################
################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", help="test setting")
    args = parser.parse_args()

    return(args)

################################################################################

def main():

    byc = {
        "pkg_path": pkg_path,
        "config": read_bycon_configs_by_name( "defaults" ),
        "args": _get_args(),
        "errors": [ ],
        "warnings": [ ]
    }

    for d in [
        "dataset_definitions",
        "filter_definitions"
    ]:
        byc.update( { d: read_bycon_configs_by_name( d ) } )

    # first pre-population w/ defaults
    these_prefs = read_local_prefs( "ontologymapsCreator", dir_path )
    for d_k, d_v in these_prefs.items():
        byc.update( { d_k: d_v } )

################################################################################

    if byc["args"].test:
        print( "¡¡¡ TEST MODE - no db update !!!")


    mongo_client = MongoClient( )
    o_m = { }

    for scope in byc["ontologymaps_prefixes"]:

        o_l_max = len(byc["ontologymaps_prefixes"][ scope ])

        for ds_id in byc["dataset_ids"]:
            data_db = mongo_client[ ds_id ]
            for coll in byc["data_collections"]:
                no =  data_db[ coll ].estimated_document_count()
                if not byc["args"].test:
                    bar = Bar("Analyzing samples", max = no, suffix='%(percent)d%%'+" of "+str(no) )
                for s in data_db[ coll ].find({}):
                    o_l_c = 0
                    k_l = [ ]
                    o_l = [ ]
                    for pre in byc["ontologymaps_prefixes"][ scope ]:
                        data_key = byc["filter_definitions"][ pre ]["db_key"]
                        list_key = re.sub(".type.id", "", data_key)
                        data_re = re.compile( byc["filter_definitions"][ pre ]["pattern_strict"] )

                        for o in s[ list_key ]:
                            if data_re.match( o["type"]["id"] ):
                                k_l.append( o["type"]["id"] )
                                o_l.append( o["type"] )
                                o_l_c += 1
                                if o_l_max > o_l_c:
                                    break
                                d = ""
                                if "description" in s:
                                    d = s["description"]
                                k = "::".join(k_l)
                                if byc["args"].test:
                                    print(k)
                                o_m.update(
                                    { k:
                                        { 
                                            "id": k,
                                            "example": d,
                                            "biocharacteristics": o_l
                                        }

                                    }
                                )
                    if not byc["args"].test:
                        bar.next()
                if not byc["args"].test:
                    bar.finish()
                        
        print("{} code combinations for {}".format(len(o_m.keys()), scope))

    if not byc["args"].test:
        om_coll = mongo_client[ byc["config"]["info_db"] ][ byc["config"]["ontologymaps_coll"] ]
        om_coll.drop()
        om_coll.insert_many( o_m.values() )
        print("==> Rewrote {}.{} collection".format(byc["config"]["info_db"], byc["config"]["ontologymaps_coll"]))

################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    main()
