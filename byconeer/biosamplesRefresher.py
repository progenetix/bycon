#!/usr/local/bin/python3

import re, json, yaml
from os import path, environ, pardir
import sys, datetime
from isodate import date_isoformat
from pymongo import MongoClient
import argparse
import statistics
from progress.bar import Bar

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_sub = path.dirname(__file__)
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer.lib import *

"""

## `biosamplesRefresher`

* `biosamplesRefresher.py -d progenetix -m stats`

"""

################################################################################
################################################################################
################################################################################

def _get_args(byc):

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datasetids", help="datasets, comma-separated")
    parser.add_argument("-a", "--alldatasets", action='store_true', help="process all datasets")
    parser.add_argument("-f", "--filters", help="prefixed filter values, comma concatenated")
    parser.add_argument("-t", "--test", help="test setting")
    parser.add_argument('-i', '--inputfile', help='a custom file to specify input data')
    parser.add_argument('-m', '--mode', help='update modus')
    byc.update({ "args": parser.parse_args() })

    return byc

################################################################################

def main():

    biosamples_refresher()

################################################################################

def biosamples_refresher():

    byc = initialize_service()
    _get_args(byc)

    if byc["args"].test:
        print( "¡¡¡ TEST MODE - no db update !!!")

    select_dataset_ids(byc)
    check_dataset_ids(byc)
    parse_filters(byc)
    parse_variants(byc)
    initialize_beacon_queries(byc)

    generate_genomic_intervals(byc)

    if len(byc["dataset_ids"]) < 1:
        print("No existing dataset was provided with -d ...")
        exit()

    generate_genomic_intervals(byc)
    pub_labels = _map_publication_labels(byc)

    for ds_id in byc["dataset_ids"]:
        _process_dataset(ds_id, pub_labels, byc)

################################################################################
################################################################################
################################################################################

def _process_dataset(ds_id, pub_labels, byc):

    no_cs_no = 0
    no_stats_no = 0

    if not ds_id in byc["config"][ "dataset_ids" ]:
        print("¡¡¡ "+ds_id+" is not a registered dataset !!!")
        return

    bios_query = {}
    if "biosamples" in byc["queries"]:
        bios_query = byc["queries"]["biosamples"]

    data_client = MongoClient( )
    data_db = data_client[ ds_id ]
    bios_coll = data_db[ "biosamples" ]
    cs_coll = data_db[ "callsets" ]
    v_coll = data_db[ "variants" ]

    bs_ids = []

    for bs in bios_coll.find (bios_query, {"id":1} ):
        bs_ids.append(bs["id"])

    no =  len(bs_ids)

    bar = Bar("{} samples from {}".format(no, ds_id), max = no, suffix='%(percent)d%%'+" of "+str(no) )

    count = 0
    for bsid in bs_ids:

        s = bios_coll.find_one({ "id":bsid })
        update_obj = {}

        _update_cnv_stats(cs_coll, bsid, update_obj, byc)

        if "sampledTissue" in s:
            if "UBERON" in s["sampledTissue"]["id"]:
                biocs = [ s["sampledTissue"] ]
                for b_c in s[ "biocharacteristics" ]:
                    if not "UBERON" in b_c["id"]:
                        biocs.append(b_c)
                update_obj.update( { "biocharacteristics": biocs } )

        if "biocharacteristics" in s:
            for b_c in s[ "biocharacteristics" ]:
                 if "NCIT:C" in b_c["id"]:
                    update_obj.update( { "histological_diagnosis": b_c } ) 

        if "external_references" in s:
            e_r_u = [ ]
            for e_r in s[ "external_references" ]:
                if "PMID" in e_r["id"]:
                    if e_r["id"] in pub_labels:
                        e_r.update( {"label": pub_labels[ e_r["id"] ] } )
                e_r_u.append(e_r)                   
            update_obj.update( { "external_references": e_r_u } ) 

        # if "pathological_tnm_findings" in s:
        #     update_obj.update( { "pathological_tnm_findings": s["pathological_tnm_findings"] } )
        # else:    
        # TODO: check existing content first  
        update_obj.update( { "pathological_tnm_findings": [] } )
        if "info" in s:
            if "tnm" in s["info"]:
                if not isinstance(s["info"]["tnm"], str):
                    continue
                for tnm_def in byc["these_prefs"]["pathologicalTnmFindings"].values():
                    if re.compile( tnm_def["pattern"] ).match( s["info"]["tnm"] ):
                        update_obj["pathological_tnm_findings"].append({
                            "id": tnm_def["id"],
                            "label": tnm_def["label"]
                        })
                        count += 1

        ####################################################################

        if not byc["args"].test:
            bios_coll.update_one( { "_id": s["_id"] }, { '$set': update_obj }  )
        
        bar.next()

    bar.finish()

    print("TNMs: {}".format(count))

################################################################################

def _map_publication_labels(byc):

    pub_client = MongoClient( )
    pub_labels = { }
    pub_db = byc["config"]["info_db"]
    pub_coll = pub_client[ pub_db ][ "publications" ]
    for pub in pub_coll.find( { "label": { "$regex": "..." } }, { "_id": 0, "id": 1, "label": 1 } ):
        pub_labels.update( { pub["id"] : pub["label"] } )

    return pub_labels

################################################################################

def _update_cnv_stats(cs_coll, bsid, update_obj, byc):

    if not byc["args"].mode:
        return update_obj
    if not "stat" in byc["args"].mode:
        return update_obj

    """
    The following code will refresh callset ids and their statistics into
    the biosamples entries.
    If no callsets are found this will result in empty attributes; if
    more than one callset is found the average of the CNV statistics will be used.
    """
    cs_ids = [ ]
    cs_stats_no = 0
    cnv_stats = { }
    cnvstatistics = {k:[] for k in byc["these_prefs"]["refreshing"]["cnvstatistics"]}
    cs_query = { "biosample_id": bsid }

    cs_ids = cs_coll.distinct( "id", cs_query )

    if len(cs_ids) < 1:
        print("\n!!! biosample {} had no callset !!!".format(s["id"]))
        return update_obj

    for cs in cs_coll.find( cs_query ):
        cs_ids.append(cs["id"])

        if "cnvstatistics" in cs["info"]:
            cs_stats_no = cs_stats_no + 1
            for s_k in cnvstatistics.keys():
                if s_k in cs["info"]["cnvstatistics"]:
                    cnvstatistics[ s_k ].append(cs["info"]["cnvstatistics"][ s_k ])

    if cs_stats_no > 0:
        for s_k in cnvstatistics.keys():
            n = len(cnvstatistics[ s_k ])
            if n > 0:
                cnv_stats[ s_k ] = sum(cnvstatistics[ s_k ]) / n
                if cnv_stats[ s_k ] < 1:
                    cnv_stats[ s_k ] = round( cnv_stats[ s_k ], 3)
                else:
                    cnv_stats[ s_k ] = int( cnv_stats[ s_k ] )

    update_obj.update( { "info.callset_ids": cs_ids, "info.cnvstatistics": cnv_stats } )

    return update_obj

################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    main()
