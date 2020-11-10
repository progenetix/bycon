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

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datasetids", help="datasets, comma-separated")
    parser.add_argument("-a", "--alldatasets", action='store_true', help="process all datasets")
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

################################################################################

    if byc["args"].alldatasets:
        dataset_ids = byc["config"][ "dataset_ids" ]
    else:
        dataset_ids =  byc["args"].datasetids.split(",")
        if not dataset_ids[0] in byc["config"][ "dataset_ids" ]:
            print("No existing dataset was provided with -d ...")
            exit()

    for ds_id in dataset_ids:
        if not ds_id in byc["config"][ "dataset_ids" ]:
            print("¡¡¡ "+ds_id+" is not a registered dataset !!!")
            continue
        print( "Creating collations for " + ds_id)

        if byc["args"].test:
            print( "¡¡¡ TEST MODE - no db update !!!")
        _create_collations_from_dataset( ds_id, **byc )

################################################################################

def _create_collations_from_dataset( ds_id, **byc ):

    coll_types = byc["config"]["collationed"]
    # coll_types = { "cellosaurus": { } }

    hiers = {}
    for pre in coll_types.keys():
        pre_h_f = path.join( dir_path, "rsrc", pre, "numbered-hierarchies.tsv" )
        if  path.exists( pre_h_f ):
            print( "Creating hierarchy for " + pre)
            hiers.update( { pre: get_prefix_hierarchy( ds_id, pre, pre_h_f, **byc) } )
        else:
            # create /retrieve hierarchy tree; method to be developed
            print( "Creating dummy hierarchy for " + pre)
            hiers.update( { pre: _get_dummy_hierarchy( ds_id, pre, **byc ) } )

    coll_client = MongoClient( )
    coll_coll = coll_client[ ds_id ][ byc["config"]["collations_coll"] ]

    if not byc["args"].test:
        coll_coll.drop()

    data_client = MongoClient( )
    data_db = data_client[ ds_id ]
    data_coll = data_db[ byc["config"]["collations_source"] ]

    for pre in coll_types.keys():

        data_key = byc["filter_definitions"][ pre ]["db_key"]

        pre_filter = re.compile( r'^'+pre )
        onto_ids = data_coll.distinct( data_key, { data_key: { "$regex": pre_filter } } )
        onto_ids = list(filter(pre_filter.match, onto_ids))

        no = len(hiers[ pre ].keys())
        ind = 0
        matched = 0
        
        if not byc["args"].test:
            bar = Bar("Writing "+pre+" to collations", max = no, suffix='%(percent)d%%'+" of "+str(no) )
        
        for code in hiers[ pre ].keys():

            if not byc["args"].test:
                bar.next()
 
            ind += 1
            children = hiers[ pre ][ code ][ "child_terms" ]
            if not list( set( children ) & set( onto_ids ) ):
                if byc["args"].test:
                    print(code+" w/o children")
                continue

            code_no = data_coll.count_documents( { data_key: code } )

            if len(children) < 2:
                child_no = code_no
            else:
                child_no =  data_coll.count_documents( { data_key: { "$in": children } } )

            hiers[ pre ][ code ].update( {
                "code_matches": code_no,
                "count": child_no,
                "date": date_isoformat(datetime.datetime.now())
            } )
 
            if child_no > 0:
                matched += 1
                if not byc["args"].test:
                    coll_coll.insert_one( hiers[ pre ][ code ] )
                else:
                    print("{}:\t{} ({} deep) samples - {} / {} {}".format(code, code_no, child_no, ind, no, pre))

        if not byc["args"].test:
            bar.finish()

        print("===> Found {} of {} {} codes & added them to {}.{} <===".format(matched, no, pre, ds_id, byc["config"]["collations_coll"]))
       
################################################################################

def get_prefix_hierarchy( ds_id, pre, pre_h_f, **byc):

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

    # now adding terms missing from the tree ###################################

    data_client = MongoClient( )
    data_db = data_client[ ds_id ]
    data_coll = data_db[ byc["config"]["collations_source"] ]
    data_key = byc["filter_definitions"][ pre ]["db_key"]
    list_key = re.sub(".type.id", "", data_key)
    
    pre_filter = re.compile( r'^'+pre )
    onto_ids = data_coll.distinct( data_key, { data_key: { "$regex": pre_filter } } )
    onto_ids = list(filter(pre_filter.match, onto_ids))

    added_no = 0
    for o in onto_ids:
        
        if o in hier.keys():
            continue

        added_no += 1
        no += 1

        l = _get_label_for_code(data_coll, data_key, o, list_key)

        if "NCIT" in pre:
            o_p = { "order": no, "depth": 1, "path": [ "NCIT:C3262", o ] }
            hier.update( { o: { "id": o, "label": l, "hierarchy_paths": [ o_p ] } } )
        else:
            o_p = { "order": no, "depth": 0, "path": [ o ] }
            hier.update( { o: { "id": o, "label": l, "hierarchy_paths": [ o_p ] } } )
        print("¡¡¡ Added missing {} {} !!!".format(o, l))

    if added_no > 0:
        print("===> Added {} {} codes from {}.{} <===".format(added_no, pre, ds_id, byc["config"]["collations_source"] ) )

    ############################################################################

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

    ############################################################################

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

def _get_dummy_hierarchy(ds_id, pre, **byc):

    data_client = MongoClient( )
    data_db = data_client[ ds_id ]
    data_coll = data_db[ byc["config"]["collations_source"] ]

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
            hier[c].update( { "child_terms": list( set(ser_ids) | set(hier[c]["child_terms"]) ) } )
   
    bar.finish()

    return hier

################################################################################

def _get_hierarchy_item(data_coll, dist, code, list_key, order, depth, path):

    return {
        "id": code,
        "label": _get_label_for_code(data_coll, dist, code, list_key),
        "hierarchy_paths": [ { "order": order, "depth": depth, "path": list(path) } ],
        "parent_terms": list(path),
        "child_terms": [ code ]
    }

################################################################################

def _get_label_for_code(data_coll, data_key, code, list_key):

    example = data_coll.find_one( { data_key: code } )

    if list_key in example.keys():
        for o_t in example[ list_key ]:
            if code in o_t["type"]["id"]:
                if "label" in o_t["type"]:
                    return o_t["type"]["label"]
                continue

    return ""

################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    main()
