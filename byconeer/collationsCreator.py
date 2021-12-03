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

from beaconServer.lib import *
from services.lib import *
"""

## `collationsCreator`

"""

################################################################################
################################################################################
################################################################################

def _get_args(byc):

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datasetids", help="datasets, comma-separated")
    parser.add_argument("-a", "--alldatasets", action='store_true', help="process all datasets")
    parser.add_argument("-t", "--test", help="test setting")
    parser.add_argument("-c", "--collationtypes", help='selected collation types, e.g. "EFO"')
   
    byc.update({ "args": parser.parse_args() })

    return byc

################################################################################

def main():
    collations_creator()

################################################################################

def collations_creator():

    byc = initialize_service()
    _get_args(byc)

    if byc["args"].test:
        print( "¡¡¡ TEST MODE - no db update !!!")

    select_dataset_ids(byc)
    check_dataset_ids(byc)

    if len(byc["dataset_ids"]) < 1:
        print("No existing dataset was provided with -d ...")
        exit()

    if byc["args"].collationtypes:
        s_p = {}
        for p in re.split(",", byc["args"].collationtypes):
            if p in byc["collation_definitions"].keys():
                s_p.update({p:byc["collation_definitions"][p]})
        if len(s_p.keys()) < 1:
            print("No existing collation type was provided with -c ...")
            exit()

        byc.update({"collation_definitions":s_p})

    for ds_id in byc["dataset_ids"]:
        print( "Creating collations for " + ds_id)
        _create_collations_from_dataset( ds_id, byc )

################################################################################

def _create_collations_from_dataset( ds_id, byc ):

    for coll_type, coll_defs in byc["collation_definitions"].items():

        pre = coll_defs["prefix"]
        pre_h_f = path.join( byc["pkg_path"], "byconeer", "rsrc", coll_type, "numbered-hierarchies.tsv" )
        collection = coll_defs["scope"]
        db_key = coll_defs["db_key"]

        if  path.exists( pre_h_f ):
            print( "Creating hierarchy for " + coll_type)
            hier =  get_prefix_hierarchy( ds_id, coll_type, pre_h_f, byc)
        elif "PMID" in pre:
            hier =  _make_dummy_publication_hierarchy(**byc)
        else:
            # create /retrieve hierarchy tree; method to be developed
            print( "Creating dummy hierarchy for " + coll_type)
            hier =  _get_dummy_hierarchy( ds_id, coll_type, coll_defs, byc )

        coll_client = MongoClient( )
        coll_coll = coll_client[ ds_id ][ byc["config"]["collations_coll"] ]

        data_client = MongoClient( )
        data_db = data_client[ ds_id ]
        data_coll = data_db[ collection ]

        onto_ids = _get_ids_for_prefix( data_coll, coll_defs )

        sel_hiers = [ ]

        # get the set of all parents for sample codes
        data_parents = set()
        for o_id in onto_ids:
            if o_id in hier.keys():
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

            code_no = data_coll.count_documents( { db_key: code } )

            if len( children ) < 2:
                child_no = code_no
            else:
                child_no =  data_coll.count_documents( { db_key: { "$in": children } } )
 
            if child_no > 0:

                # sub_id = re.sub(pre, coll_type, code)
                sub_id = code
                update_obj = hier[ code ].copy()
                update_obj.update({
                    "id": sub_id,
                    "type": coll_defs.get("type", ""),
                    "collation_type": coll_type,
                    "prefix": coll_defs.get("prefix", ""),
                    "scope": coll_defs.get("scope", ""),
                    "code_matches": code_no,
                    "code": code,
                    "count": child_no,
                    "dataset_id": ds_id,
                    "date": date_isoformat(datetime.datetime.now()),
                    "db_key": db_key
                })
                matched += 1

                if not byc["args"].test:
                    sel_hiers.append( update_obj )
                else:
                    print("{}:\t{} ({} deep) samples - {} / {} {}".format(sub_id, code_no, child_no, count, no, pre))


        # UPDATE   
        if not byc["args"].test:
            bar.finish()
            print("==> Updating database ...")
            if matched > 0:
                coll_coll.delete_many( { "collation_type": coll_type } )
                coll_coll.insert_many( sel_hiers )

        print("===> Found {} of {} {} codes & added them to {}.{} <===".format(matched, no, coll_type, ds_id, byc["config"]["collations_coll"]))
       
################################################################################

def get_prefix_hierarchy( ds_id, coll_type, pre_h_f, byc):

    coll_defs = byc["collation_definitions"][coll_type]
    hier = { }

    f = open(pre_h_f, 'r+')
    h_in  = [line for line in f.readlines()]
    f.close()

    parents = [ ]

    no = len(h_in)
    bar = Bar(coll_type, max = no, suffix='%(percent)d%%'+" of "+str(no) )

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

    print("Looking for missing {} codes in {}.{} ...".format(coll_type, ds_id, byc["config"]["collations_source"]))
    data_client = MongoClient( )
    data_db = data_client[ ds_id ]
    data_coll = data_db[coll_defs["scope"]]
    
    onto_ids = _get_ids_for_prefix( data_coll, coll_defs )

    added_no = 0

    if coll_type == "NCIT":
        added_no += 1
        no += 1
        hier.update( {
            "NCIT:C000000": {
                "id": "NCIT:C000000",
                "label": "Unplaced Entities",
                "type": coll_defs.get("type", ""),
                "collation_type": coll_type,
                "prefix": coll_defs.get("prefix", ""),
                "scope": coll_defs.get("scope", ""),
                "db_key": coll_defs.get("db_key", ""),
                "hierarchy_paths": [ { "order": no, "depth": 1, "path": [ "NCIT:C3262", "NCIT:C000000" ] } ]
            }
        } )

    for o in onto_ids:
        
        if o in hier.keys():
            continue

        added_no += 1
        no += 1

        l = _get_label_for_code(data_coll, coll_defs, o)

        if coll_type == "NCIT":
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
        print("===> Added {} {} codes from {}.{} <===".format(added_no, coll_type, ds_id, byc["config"]["collations_source"] ) )

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

    coll_type = "PMID"
    coll_defs = byc["collation_definitions"][coll_type]
    data_db = byc["config"]["info_db"]
    data_coll = MongoClient( )[ data_db ][ "publications" ]
    query = { "id": { "$regex": coll_defs["pattern"] } }

    hier = { }

    no = data_coll.count_documents( query )
    bar = Bar("Publications...", max = no, suffix='%(percent)d%%'+" of "+str(no) )

    for order, pub in enumerate( data_coll.find( query, { "_id": 0 } ) ):
        code = pub["id"]
        bar.next()
        hier.update( { 
            code: {
                "id":  code,
                "label": pub["label"],
                "type": coll_defs.get("type", ""),
                "collation_type": coll_type,
                "prefix": coll_defs.get("prefix", ""),
                "scope": coll_defs.get("scope", ""),
                "db_key": coll_defs.get("db_key", ""),
                "hierarchy_paths": [ { "order": int(order), "depth": 0, "path": [ code ] } ],
                "parent_terms": [ code ],
                "child_terms": [ code ]
            }
        } )
 
    bar.finish()

    return hier

################################################################################

def _get_dummy_hierarchy(ds_id, coll_type, coll_defs, byc):

    data_client = MongoClient( )
    data_db = data_client[ ds_id ]
    data_coll = data_db[ coll_defs["scope"] ]
    data_pat = coll_defs["pattern"]
    db_key = coll_defs["db_key"]

    if coll_defs["is_series"]: 
        s_pat = coll_defs["child_pattern"]
        s_re = re.compile( s_pat )

    pre_ids = _get_ids_for_prefix( data_coll, coll_defs )

    hier = { }
    no = len(pre_ids)
    bar = Bar(coll_type, max = no, suffix='%(percent)d%%'+" of "+str(no) )

    for order, c in enumerate(sorted(pre_ids), start=1):

        bar.next()
        hier.update( { c: _get_hierarchy_item( data_coll, coll_defs, coll_type, c, order, 0, [ c ] ) } )

        if coll_defs["is_series"]:

            ser_ids = data_coll.distinct( db_key, { db_key: c } )
            ser_ids = list(filter(lambda d: s_re.match(d), ser_ids))
            hier[c].update( { "child_terms": list( set(ser_ids) | set(hier[c]["child_terms"]) ) } )
   
    bar.finish()

    return hier

################################################################################

def _get_hierarchy_item(data_coll, coll_defs, coll_type, code, order, depth, path):

    return {
        "id":  code,
        "label": _get_label_for_code(data_coll, coll_defs, code),
        "type": coll_defs.get("type", ""),
        "collation_type": coll_type,
        "prefix": coll_defs.get("prefix", ""),
        "scope": coll_defs.get("scope", ""),
        "db_key": coll_defs.get("db_key", ""),
        "hierarchy_paths": [ { "order": int(order), "depth": int(depth), "path": list(path) } ],
        "parent_terms": list(path),
        "child_terms": [ code ]
    }

################################################################################

def _get_ids_for_prefix(data_coll, coll_defs):

    db_key = coll_defs["db_key"]
    pre_re = re.compile( coll_defs["pattern"] )

    pre_ids = data_coll.distinct( db_key, { db_key: { "$regex": pre_re } } )
    pre_ids = list(filter(lambda d: pre_re.match(d), pre_ids))

    return pre_ids

################################################################################

def _get_label_for_code(data_coll, coll_defs, code):

    db_key = coll_defs["db_key"]
    id_key = re.sub(".id", "", db_key)
    example = data_coll.find_one( { db_key: code } )

    if id_key in example.keys():
        if isinstance(example[ id_key ], list):
            for o_t in example[ id_key ]:
                if code in o_t["id"]:
                    if "label" in o_t:
                        return o_t["label"]
                    continue
        else:
            o_t = example[ id_key ]
            if code in o_t["id"]:
                if "label" in o_t:
                    return o_t["label"]

    return ""

################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    main()
