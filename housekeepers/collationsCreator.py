#!/usr/bin/env python3

import datetime, json, re, sys, yaml
from os import path, environ, pardir
from pymongo import MongoClient
from progress.bar import Bar

from bycon import BYC, config, initialize_bycon_service, prdbug
from byconServiceLibs import assertSingleDatasetOrExit, hierarchy_from_file, set_collation_types, write_log

dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )


"""
## `collationsCreator`

"""

################################################################################
################################################################################
################################################################################

def main():
    ds_id = assertSingleDatasetOrExit()

    print(f'Creating collations for {ds_id}')

    set_collation_types()
    f_d_s = BYC["filter_definitions"].get("$defs", {})
    
    for coll_type, coll_defs in f_d_s.items():
        collationed = coll_defs.get("collationed")
        if not collationed:
            continue
        __process_collation_type(ds_id, coll_type, coll_defs)


################################################################################

def __process_collation_type(ds_id, coll_type, coll_defs):
    pre_h_f = path.join( pkg_path, "rsrc", "classificationTrees", coll_type, "numbered_hierarchies.tsv" )
    pre_c_f = path.join( pkg_path, "logs", "inventory", f'{ds_id}_{coll_type}_existing_codes.tsv' )
    collection = coll_defs["scope"]
    db_key = coll_defs["db_key"]

    if "pubmed" in coll_type:
        hier =  __make_dummy_publication_hierarchy()
    elif path.exists( pre_h_f ):
        print( "Creating hierarchy for " + coll_type)
        hier =  get_prefix_hierarchy(ds_id, coll_type, pre_h_f)
    else:
        # create /retrieve hierarchy tree; method to be developed
        print( "Creating dummy hierarchy for " + coll_type)
        hier =  __get_dummy_hierarchy(ds_id, coll_type, coll_defs)

    coll_coll = MongoClient(host=config.DB_MONGOHOST)[ ds_id ]["collations"]
    data_coll = MongoClient(host=config.DB_MONGOHOST)[ ds_id ][ collection ]

    onto_ids = __get_ids_for_prefix( data_coll, coll_defs )
    onto_keys = list( set(onto_ids) & hier.keys() )

    # get the set of all parents for sample codes
    onto_keys = set()
    for o_id in onto_ids:
        if o_id in hier.keys():
            onto_keys.update( hier[o_id][ "parent_terms" ] )

    sel_hiers = {}
    no = len(hier.keys())
    matched = 0
    if not BYC["TEST_MODE"]:
        bar = Bar("Writing "+coll_type, max = no, suffix='%(percent)d%%'+" of "+str(no) )      
    for count, c_id in enumerate(hier.keys(), start=1):
        if not BYC["TEST_MODE"]:
            bar.next()
        children = list(set(hier[c_id]["child_terms"]) & onto_keys)
        hier[c_id].update( {"child_terms": children})
        if len( children ) < 1:
            if BYC["TEST_MODE"]:
                print(c_id+" w/o children")
            continue
        code_no = data_coll.count_documents({db_key: c_id})
        if code_no < 1:
            code_no = 0
        if len(children) < 2:
            child_no = code_no
        else:
            child_no =  data_coll.count_documents( { db_key: { "$in": children } } )
        if child_no > 0:
            update_obj = hier[c_id].copy()
            update_obj.update({
                "id": c_id,
                "ft_type": coll_defs.get("ft_type", "ontologyTerm"),
                "name": coll_defs.get("name", ""),
                "collation_type": coll_type,
                "reference": "https://progenetix.org/services/ids/"+c_id,
                "namespace_prefix": coll_defs.get("namespace_prefix", ""),
                "scope": coll_defs.get("scope", ""),
                "entity": coll_defs.get("entity", ""),
                "code_matches": code_no,
                "count": child_no,
                "dataset_id": ds_id,
                "updated": datetime.datetime.now().isoformat(),
                "db_key": db_key
            })
            if "reference" in coll_defs:
                url = coll_defs["reference"].get("root", "https://progenetix.org/services/ids/")
                r = coll_defs["reference"].get("replace", ["___nothing___", ""])
                ref = url+re.sub(r[0], r[1], c_id)
                update_obj.update({"reference": ref })
            matched += 1
            if not BYC["TEST_MODE"]:
                sel_hiers.update({c_id: update_obj})
            else:
                print(f'{c_id}:\t{code_no} ({child_no} deep) samples - {count} / {no} {coll_type}')
    # UPDATE   
    if not BYC["TEST_MODE"]:
        bar.finish()
        if matched > 0:
            codes = []
            print("==> Updating database ...")
            ex_codes = coll_coll.distinct("id", { "collation_type": coll_type })
            for ex_c in ex_codes:
                if ex_c not in sel_hiers.keys():
                    coll_coll.delete_one( { "id": ex_c } )
            for coll_id, update_obj in sel_hiers.items():
                coll_coll.update_one( { "id": coll_id }, { "$set": update_obj }, upsert=True )
                if (c := update_obj.get("code_matches", 0)) > 0:
                    codes.append( f'{coll_id}\t{update_obj.get("label","")}\t{c}' )
            print("==> Writing Codes ...")
            write_log(codes, pre_c_f, "")

    print(f'===> Found {matched} of {no} {coll_type} codes & added them to {ds_id}.collations <===')

     
################################################################################

def get_prefix_hierarchy(ds_id, coll_type, pre_h_f):
    f_d_s = BYC["filter_definitions"].get("$defs", {})

    if not (coll_defs := f_d_s.get(coll_type)):
        print(f'¡¡¡ missing {coll_type} !!!')
        return

    hier = hierarchy_from_file(ds_id, coll_type, pre_h_f)
    no = len(hier.keys())

    # now adding terms missing from the tree ###################################
    print("Looking for missing {} codes in {}.{} ...".format(coll_type, ds_id, coll_defs["scope"]))

    data_coll = MongoClient(host=config.DB_MONGOHOST)[ ds_id ][coll_defs["scope"]]
    db_key = coll_defs.get("db_key", "")    
    onto_ids = __get_ids_for_prefix( data_coll, coll_defs )

    added_no = 0

    if coll_type == "NCIT":
        added_no += 1
        no += 1
        hier.update( {
            "NCIT:C000000": {
                "id": "NCIT:C000000",
                "label": "Unplaced Entities",
                "ft_type": "ontologyTerm",
                "name": "NCI Thesaurus OBO Edition",
                "collation_type": coll_type,
                "namespace_prefix": coll_defs.get("namespace_prefix", ""),
                "scope": coll_defs.get("scope", ""),
                "entity": coll_defs.get("entity", ""),
                "db_key": coll_defs.get("db_key", ""),
                "hierarchy_paths": [ { "order": no, "depth": 1, "path": [ "NCIT:C3262", "NCIT:C000000" ] } ]
            }
        } )

    for c_id in onto_ids:
        if c_id in hier.keys():
            continue
        added_no += 1
        no += 1
        l = __get_label_for_code(data_coll, coll_defs, c_id)
        if coll_type == "NCIT":
            hier.update( {
                    c_id: { "id": c_id, "label": l, "hierarchy_paths":
                        [ { "order": int(no), "depth": 3, "path": [ "NCIT:C3262", "NCIT:C000000", c_id ] } ]
                    }
                }
            )
        else:
            o_p = { "order": int(no), "depth": 0, "path": [ c_id ] }
            hier.update( { c_id: { "id": c_id, "label": l, "hierarchy_paths": [ o_p ] } } )
        print("Added:\t{}\t{}".format(c_id, l))
    if added_no > 0:
        print("===> Added {} {} codes from {}.{} <===".format(added_no, coll_type, ds_id, coll_defs["scope"] ) )

    #--------------------------------------------------------------------------#

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

    #--------------------------------------------------------------------------#

    bar = Bar("    parsing children ", max = no, suffix='%(percent)d%%'+" of "+str(no) )
    for c, h in hier.items():
        bar.next()
        all_children = set()
        for c_2, h_2 in hier.items():
            if c in h_2["parent_terms"]:
                all_children.add( c_2 )
        hier[c].update({"child_terms": list(all_children)})
    bar.finish()

    return hier

################################################################################

def __make_dummy_publication_hierarchy():
    f_d_s = BYC["filter_definitions"].get("$defs", {})
    coll_type = "pubmed"
    coll_defs = f_d_s[coll_type]
    data_coll = MongoClient(host=config.DB_MONGOHOST)["_byconServicesDB"]["publications"]
    query = { "id": { "$regex": r'^PMID\:\d+?$' } }
    no = data_coll.count_documents( query )
    bar = Bar("Publications...", max = no, suffix='%(percent)d%%'+" of "+str(no) )

    hier = {}

    for order, pub in enumerate( data_coll.find( query, { "_id": 0 } ) ):
        c_id = pub["id"]
        bar.next()
        hier.update( { 
            c_id: {
                "id":  c_id,
                "label": pub["label"],
                "ft_type": "ontologyTerm",
                "name": "NCBI PubMed",
                "collation_type": coll_type,
                "namespace_prefix": coll_defs.get("namespace_prefix", ""),
                "scope": coll_defs.get("scope", ""),
                "entity": coll_defs.get("entity", ""),
                "db_key": coll_defs.get("db_key", ""),
                "updated": datetime.datetime.now().isoformat(),
                "hierarchy_paths": [ { "order": int(order), "depth": 0, "path": [ c_id ] } ],
                "parent_terms": [ c_id ],
                "child_terms": [ c_id ]
            }
        } )
    bar.finish()
    return hier

################################################################################

def __get_dummy_hierarchy(ds_id, coll_type, coll_defs):
    data_db = MongoClient(host=config.DB_MONGOHOST)[ ds_id ]
    data_coll = data_db[ coll_defs["scope"] ]
    data_pat = coll_defs["pattern"]
    db_key = coll_defs["db_key"]

    pre_ids = __get_ids_for_prefix(data_coll, coll_defs)
    hier = { }
    no = len(pre_ids)
    bar = Bar(coll_type, max = no, suffix='%(percent)d%%'+" of "+str(no) )

    for order, c_id in enumerate(sorted(pre_ids), start=1):
        bar.next()
        hier.update( { c_id: __get_hierarchy_item( data_coll, coll_defs, coll_type, c_id, order, 0, [ c_id ] ) } )
   
    bar.finish()
    return hier


################################################################################

def __get_hierarchy_item(data_coll, coll_defs, coll_type, c_id, order, depth, path):

    return {
        "id":  c_id,
        "label": __get_label_for_code(data_coll, coll_defs, c_id),
        "ft_type": coll_defs.get("ft_type", ""),
        "collation_type": coll_type,
        "namespace_prefix": coll_defs.get("namespace_prefix", ""),
        "scope": coll_defs.get("scope", ""),
        "entity": coll_defs.get("entity", ""),
        "db_key": coll_defs.get("db_key", ""),
        "updated": datetime.datetime.now().isoformat(),
        "hierarchy_paths": [ { "order": int(order), "depth": int(depth), "path": list(path) } ],
        "parent_terms": list(path),
        "child_terms": [ c_id ]
    }

################################################################################

def __get_ids_for_prefix(data_coll, coll_defs):

    db_key = coll_defs["db_key"]
    pre_re = re.compile( coll_defs["pattern"] )

    prdbug(f'__get_ids_for_prefix ... : "{db_key}"" - pattern {pre_re}')
    pre_ids = data_coll.distinct( db_key, { db_key: { "$regex": pre_re } } )
    pre_ids = list(filter(lambda d: pre_re.match(d), pre_ids))
    prdbug(f'__get_ids_for_prefix ... : found {len(pre_ids)}')

    return pre_ids

################################################################################

def _get_child_ids_for_prefix(data_coll, coll_defs):

    child_ids = []

    if not "series_pattern" in coll_defs:
        return child_ids

    db_key = coll_defs["db_key"]

    child_re = re.compile( coll_defs["series_pattern"] )

    child_ids = data_coll.distinct( db_key, { db_key: { "$regex": child_re } } )
    child_ids = list(filter(lambda d: child_re.match(d), child_ids))

    return child_ids


################################################################################

def __get_label_for_code(data_coll, coll_defs, c_id):

    label_keys = ["label", "description", "note"]

    db_key = coll_defs["db_key"]
    id_key = re.sub(".id", "", db_key)
    example = data_coll.find_one( { db_key: c_id } )

    if id_key in example.keys():
        if isinstance(example[ id_key ], list):
            for o_t in example[ id_key ]:
                if c_id in o_t["id"]:
                    for k in label_keys:
                        if k in o_t:
                            return o_t[k]
                    continue
        elif type(example[ id_key ]) is object:
            o_t = example[ id_key ]
            if c_id in o_t.get("id", "___none___"):
                for k in label_keys:
                        if k in o_t:
                            return o_t[k]

    return c_id


################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    main()
