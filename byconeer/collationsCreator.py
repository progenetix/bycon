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

    return args

################################################################################

def main():

    byc = {
        "pkg_path": pkg_path,
        "args": _get_args(),
        "errors": [ ],
        "warnings": [ ]
    }

    for d in [
        "config",
        "dataset_definitions",
        "filter_definitions"
    ]:
        byc.update( { d: read_bycon_configs_by_name( d ) } )

################################################################################

    if byc["args"].test:
        print( "¡¡¡ TEST MODE - no db update !!!")

    if byc["args"].alldatasets:
        dataset_ids = byc["config"][ "dataset_ids" ]
    elif byc["args"].datasetids:
        dataset_ids =  byc["args"].datasetids.split(",")
        if not dataset_ids[0] in byc["config"][ "dataset_ids" ]:
            print("No existing dataset was provided with -d ...")
            exit()
    else:
        dataset_ids = [ ]

    if len(dataset_ids) < 1:
        print("No existing dataset was provided with -d and -a wasn't invoked ...")
        exit()

    for ds_id in dataset_ids:
        if not ds_id in byc["config"][ "dataset_ids" ]:
            print("¡¡¡ "+ds_id+" is not a registered dataset !!!")
            continue
        print( "Creating collations for " + ds_id)

        _create_collations_from_dataset( ds_id, **byc )

################################################################################

def _create_collations_from_dataset( ds_id, **byc ):

    coll_types = byc["config"]["collationed"]
    # coll_types = { "NCIT": { } }
    # coll_types = { "PMID": { } }

    for pre in coll_types.keys():

        pre_h_f = path.join( dir_path, "rsrc", pre, "numbered-hierarchies.tsv" )
        if  path.exists( pre_h_f ):
            print( "Creating hierarchy for " + pre)
            hier =  get_prefix_hierarchy( ds_id, pre, pre_h_f, **byc)
        elif "PMID" in pre:
            hier =  _make_dummy_publication_hierarchy(**byc)
        else:
            # create /retrieve hierarchy tree; method to be developed
            print( "Creating dummy hierarchy for " + pre)
            hier =  _get_dummy_hierarchy( ds_id, pre, **byc )

        coll_client = MongoClient( )
        coll_coll = coll_client[ ds_id ][ byc["config"]["collations_coll"] ]

        data_client = MongoClient( )
        data_db = data_client[ ds_id ]
        data_coll = data_db[ byc["config"]["collations_source"] ]

        data_key = byc["filter_definitions"][ pre ]["db_key"]
        data_pat = byc["filter_definitions"][ pre ]["pattern_strict"]
        onto_ids = _get_ids_for_prefix( data_coll, data_key, data_pat )

        sel_hiers = [ ]

        # get the set of all parents for sample codes
        data_parents = set()
        for o_id in onto_ids:
            if o_id in hier:
                data_parents.update( hier[ o_id ][ "parent_terms" ] )

        no = len(hier.keys())
        matched = 0
        
        if not byc["args"].test:
            bar = Bar("Writing "+pre, max = no, suffix='%(percent)d%%'+" of "+str(no) )
        
        for count, code in enumerate(hier.keys(), start=1):

            if not byc["args"].test:
                bar.next()
 
            children = list( set( hier[ code ][ "child_terms" ] ) & set( data_parents ) )
            hier[ code ].update(  { "child_terms": children } )

            if len( children ) < 1:
                if byc["args"].test:
                    print(code+" w/o children")
                continue

            code_no = data_coll.count_documents( { data_key: code } )

            if len( children ) < 2:
                child_no = code_no
            else:
                child_no =  data_coll.count_documents( { data_key: { "$in": children } } )
 
            if child_no > 0:
                hier[ code ].update( {
                    "code_matches": code_no,
                    "count": child_no,
                    "date": date_isoformat(datetime.datetime.now())
                } )
                matched += 1

                if not byc["args"].test:
                    sel_hiers.append( hier[ code ] )
                else:
                    print("{}:\t{} ({} deep) samples - {} / {} {}".format(code, code_no, child_no, count, no, pre))

        if not byc["args"].test:
            bar.finish()
            print("==> Updating database ...")
            if matched > 0:
                coll_clean_q = { "id": { "$regex": "^"+pre } }
                coll_coll.delete_many( coll_clean_q )
                coll_coll.insert_many( sel_hiers )

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

    print("Looking for missing {} codes in {}.{} ...".format(pre, ds_id, byc["config"]["collations_source"]))
    data_client = MongoClient( )
    data_db = data_client[ ds_id ]
    data_coll = data_db[ byc["config"]["collations_source"] ]
    data_key = byc["filter_definitions"][ pre ]["db_key"]
    data_pat = byc["config"]["collationed"][ pre ]["pattern"]
    
    onto_ids = _get_ids_for_prefix( data_coll, data_key, data_pat )

    added_no = 0

    if "NCIT" in pre:
        added_no += 1
        no += 1
        hier.update( {
            "NCIT:C000000": {
                "id": "NCIT:C000000",
                "label": "Unplaced Entities",
                "hierarchy_paths": [ { "order": no, "depth": 1, "path": [ "NCIT:C3262", "NCIT:C000000" ] } ]
            }
        } )

    for o in onto_ids:
        
        if o in hier.keys():
            continue

        added_no += 1
        no += 1

        l = _get_label_for_code(data_coll, data_key, o)

        if "NCIT" in pre:
            hier.update( {
                    o: { "id": o, "label": l, "hierarchy_paths":
                        [ { "order": no, "depth": 3, "path": [ "NCIT:C3262", "NCIT:C000000", o ] } ]
                    }
                }
            )
        else:
            o_p = { "order": no, "depth": 0, "path": [ o ] }
            hier.update( { o: { "id": o, "label": l, "hierarchy_paths": [ o_p ] } } )
        print("Added:\t{}\t{}".format(o, l))

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

def _make_dummy_publication_hierarchy(**byc):

    mongo_client = MongoClient( )
    pub_db = byc["config"]["info_db"]
    mongo_coll = mongo_client[ pub_db ][ "publications" ]
    query = { "id": { "$regex": byc["filter_definitions"]["PMID"]["pattern"] } }

    hier = { }

    no = mongo_coll.count_documents( query )
    bar = Bar("Publications...", max = no, suffix='%(percent)d%%'+" of "+str(no) )

    for order, pub in enumerate( mongo_coll.find( query, { "_id": 0 } ) ):
        code = pub["id"]
        bar.next()
        hier.update( { 
            code: {
                "id":  code,
                "label": pub["label"],
                "hierarchy_paths": [ { "order": int(order), "depth": 0, "path": [ code ] } ],
                "parent_terms": [ code ],
                "child_terms": [ code ]
            }
        } )
 
    bar.finish()

    return hier

################################################################################

def _get_dummy_hierarchy(ds_id, pre, **byc):

    data_client = MongoClient( )
    data_db = data_client[ ds_id ]
    data_coll = data_db[ byc["config"]["collations_source"] ]
    data_pat = byc["config"]["collationed"][ pre ]["pattern"]
    data_key = byc["filter_definitions"][ pre ]["db_key"]

    if byc["config"]["collationed"][ pre ]["is_series"]: 
        s_pat = byc["config"]["collationed"][ pre ]["child_pattern"]
        s_re = re.compile( s_pat )

    pre_ids = _get_ids_for_prefix( data_coll, data_key, data_pat )

    hier = { }
    no = len(pre_ids)
    bar = Bar(pre, max = no, suffix='%(percent)d%%'+" of "+str(no) )

    for order, c in enumerate(sorted(pre_ids), start=1):

        bar.next()
        hier.update( { c: _get_hierarchy_item( data_coll, data_key, c, order, 0, [ c ] ) } )

        if byc["config"]["collationed"][ pre ]["is_series"]:

            ser_ids = data_coll.distinct( data_key, { data_key: c } )
            ser_ids = list(filter(lambda d: s_re.match(d), ser_ids))
            hier[c].update( { "child_terms": list( set(ser_ids) | set(hier[c]["child_terms"]) ) } )
   
    bar.finish()

    return hier

################################################################################

def _get_hierarchy_item(data_coll, data_key, code, order, depth, path):

    return {
        "id": code,
        "label": _get_label_for_code(data_coll, data_key, code),
        "hierarchy_paths": [ { "order": int(order), "depth": int(depth), "path": list(path) } ],
        "parent_terms": list(path),
        "child_terms": [ code ]
    }

################################################################################

def _get_ids_for_prefix(data_coll, data_key, data_pat):

    pre_re = re.compile( data_pat )
    pre_ids = data_coll.distinct( data_key, { data_key: { "$regex": pre_re } } )
    pre_ids = list(filter(lambda d: pre_re.match(d), pre_ids))

    return pre_ids

################################################################################

def _get_label_for_code(data_coll, data_key, code):
    list_key = re.sub(".id", "", data_key)
    example = data_coll.find_one( { data_key: code } )

    if list_key in example.keys():
        for o_t in example[ list_key ]:
            if code in o_t["id"]:
                if "label" in o_t:
                    return o_t["label"]
                continue

    return ""

################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    main()
