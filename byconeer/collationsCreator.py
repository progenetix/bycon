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
from bycon.lib.read_specs import read_bycon_configs_by_name
from lib.filter_aggregation  import dataset_count_collationed_filters
"""

## `collationsCreator`

"""

################################################################################
################################################################################
################################################################################

def main():

    byc = {
        "pkg_path": pkg_path,
        "dataset_id": "progenetix",
        "datacoll": "biosamples",
        "config": read_bycon_configs_by_name( "defaults" ),
        "errors": [ ],
        "warnings": [ ]
    }

    for d in [
        "dataset_definitions",
        "filter_definitions"
    ]:
        byc.update( { d: read_bycon_configs_by_name( d ) } )

################################################################################

    coll_types = byc["config"]["collationed"]
    # coll_types = { "cellosaurus":  {} }
    hiers = {}
    for pre in coll_types.keys():
        pre_h_f = path.join( dir_path, "rsrc", pre, "numbered-hierarchies.tsv" )
        if  path.exists( pre_h_f ):
            print( "Creating hierarchy for " + pre)
            hiers.update( { pre: get_prefix_hierarchy(pre, pre_h_f, **byc) } )
        else:
            # create /retrieve hierarchy tree; method to be developed
            print( "Creating dummy hierarchy for " + pre)
            hiers.update( { pre: get_dummy_hierarchy(pre, **byc) } )

    coll_client = MongoClient( )
    coll_coll = coll_client[ byc["config"]["info_db"] ][ byc["config"]["collations_coll"] ]
    coll_coll.drop()

    data_client = MongoClient( )
    data_coll = data_client[ byc["dataset_id"] ][ byc["datacoll"] ]

    for pre in coll_types.keys():

        no = len(hiers[ pre ].keys())
        bar = Bar("Writing "+pre+" to collations", max = no, suffix='%(percent)d%%'+" of "+str(no) )
        
        data_key = byc["filter_definitions"][ pre ]["db_key"]

        for code in hiers[ pre ].keys():
            bar.next()
            c_no =  data_coll.find( { data_key: code } ).count()
            hiers[ pre ][ code ].update( { "code_matches": c_no } )
            # print("{}: {}".format(code, hiers[ pre ][ code ]["code_matches"]))
            coll_coll.insert_one( hiers[ pre ][ code ] )

        bar.finish()
        

################################################################################

def get_prefix_hierarchy(pre, pre_h_f, **byc):

    hier = { }

    f = open(pre_h_f, 'r+')
    h_in  = [line for line in f.readlines()]
    f.close()

    parents = [ ]

    no = len(h_in)
    bar = Bar(pre, max = no, suffix='%(percent)d%%'+" of "+str(no) )

    for c_l in h_in:

        bar.next()

        c, l, d, i = re.split("\t", c_l.rstrip() )
        d = int(d)

        max_p = len(parents) - 1
        if max_p < d:
            parents.append(c)
        else:
            # if recursing to a lower column/hierarchy level, all deeper "parent" 
            # values are discarded
            parents[ d ] = c
            while max_p > d:
                parents.pop()
                max_p -= 1

        l_p = { "order": i, "depth": d, "path": parents.copy() }

        if not c in hier.keys():
            hier.update( { c: { "id": c, "label": l, "hierarchy_paths": [ l_p ] } } )
        else:
            hier[ c ]["hierarchy_paths"].append( l_p )
    bar.finish()

    no = len(hier)
    bar = Bar("    parsing parents ", max = no, suffix='%(percent)d%%'+" of "+str(no) )

    for c, h in hier.items():
        bar.next()
        all_parents = { }
        for h_p in h["hierarchy_paths"]:
            for parent in h_p["path"]:
                all_parents.update( { parent: 1 } )
        hier[ c ].update( { "parent_terms": list(all_parents.keys()) } )

    bar.finish()

    bar = Bar("    parsing children ", max = no, suffix='%(percent)d%%'+" of "+str(no) )
    for c, h in hier.items():
        bar.next()
        all_children = { }
        for c_2, h_2 in hier.items():
            if c in h_2["parent_terms"]:
                all_children.update( { c_2: 1 } )
        hier[ c ].update( { "child_terms": list( all_children.keys() ) } )
    
    bar.finish()

    return hier

################################################################################

def get_dummy_hierarchy(pre, **byc):

    mongo_client = MongoClient( )
    data_db = mongo_client[ byc["dataset_id"] ]
    data_coll = data_db[ byc["datacoll"] ]

    pattern = byc["config"]["collationed"][ pre ]["pattern"]
    pre_re = re.compile( pattern )

    if byc["config"]["collationed"][ pre ]["is_series"]: 
        s_pat = byc["config"]["collationed"][ pre ]["child_pattern"]
        s_re = re.compile( s_pat )

    dist_key = byc["filter_definitions"][ pre ]["db_key"]
    list_key = re.sub(".type.id", "", dist_key)

    pre_ids = data_coll.distinct( dist_key, { dist_key: { "$regex": pre_re } } )
    pre_ids = list(filter(lambda d: pre_re.match(d), pre_ids))

    hier = { }
    no = len(pre_ids)
    bar = Bar(pre, max = no, suffix='%(percent)d%%'+" of "+str(no) )
    order = 0

    for c in sorted(pre_ids):

        bar.next()
        order += 1
        hier.update( { c: _get_hierarchy_item( data_coll, dist_key, c, list_key, order, 0, [ c ] ) } )

        if byc["config"]["collationed"][ pre ]["is_series"]:

            ser_ids = data_coll.distinct( dist_key, { dist_key: c } )
            ser_ids = list(filter(lambda d: s_re.match(d), ser_ids))

            for s in sorted(ser_ids):

                order += 1
                ser_item = _get_hierarchy_item( data_coll, dist_key, s, list_key, order, 1, [c,s] )

                if s in hier:
                    hier[s].update(
                        { 
                            "parent_terms": list( set(hier[s]["parent_terms"]) | set(ser_item["parent_terms"]) ),
                            "child_terms": list( set(hier[s]["child_terms"]) | set(ser_item["child_terms"]) )
                        }
                    )
                    hier[s]["hierarchy_paths"].append( ser_item["hierarchy_paths"][0] )
                else:
                    hier.update( { s: ser_item } )
   
    bar.finish()

    return hier

################################################################################

def _get_hierarchy_item(data_coll, dist, code, list_key, order, depth, path):

    example = data_coll.find_one( { dist: code } )

    l = ""
    if list_key in example.keys():
        for o_t in example[ list_key ]:
            if code in o_t["type"]["id"]:
                if "label" in o_t["type"]:
                    l = o_t["type"]["label"]
                continue

    return {
        "id": code,
        "label": l,
        "hierarchy_paths": [ { "order": order, "depth": depth, "path": list(path) } ],
        "parent_terms": list(path),
        "child_terms": [ code ]
    }


################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    main()
