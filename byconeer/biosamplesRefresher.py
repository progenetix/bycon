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
from bycon.lib.read_specs import *
from lib.schemas_parser import *

service_lib_path = path.join( pkg_path, "services", "lib" )
sys.path.append( service_lib_path )

from service_utils import initialize_service

"""

## `biosamplesRefresher`

"""

################################################################################
################################################################################
################################################################################

def _get_args(byc):

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datasetids", help="datasets, comma-separated")
    parser.add_argument("-a", "--alldatasets", action='store_true', help="process all datasets")
    parser.add_argument("-t", "--test", help="test setting")
    byc.update({ "args": parser.parse_args() })

    return byc

################################################################################

def main():

    biosamples_refresher()

################################################################################

def biosamples_refresher():

    byc = initialize_service()
    _get_args(byc)

################################################################################

    if byc["args"].test:
        print( "¡¡¡ TEST MODE - no db update !!!")

    dataset_ids = [ ]
    if byc["args"].alldatasets:
        dataset_ids = byc["config"][ "dataset_ids" ]
    elif byc["args"].datasetids:
        dataset_ids =  byc["args"].datasetids.split(",")

    if not dataset_ids:
        print("No dataset was provided with -d ...")
        exit()

    pub_labels = _map_publication_labels(byc)

    no_cs_no = 0
    no_stats_no = 0

    for ds_id in dataset_ids:

        if not ds_id in byc["config"][ "dataset_ids" ]:
            print("¡¡¡ "+ds_id+" is not a registered dataset !!!")
            continue

        data_client = MongoClient( )
        data_db = data_client[ ds_id ]
        bios_coll = data_db[ "biosamples" ]
        cs_coll = data_db[ "callsets" ]
        no =  bios_coll.estimated_document_count()
        if not byc["args"].test:
            bar = Bar("Refreshing {}".format(ds_id), max = no, suffix='%(percent)d%%'+" of "+str(no) )
        for s in bios_coll.find({}):

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
            cs_query = { "biosample_id": s["id"] }
            for cs in cs_coll.find( cs_query ):
                cs_ids.append(cs["id"])
                if "cnvstatistics" in cs["info"]:
                    cs_stats_no = cs_stats_no + 1
                    for s_k in cnvstatistics.keys():
                        if s_k in cs["info"]["cnvstatistics"]:
                            cnvstatistics[ s_k ].append(cs["info"]["cnvstatistics"][ s_k ])
            any_stats = False
            if cs_stats_no > 0:
                for s_k in cnvstatistics.keys():
                    n = len(cnvstatistics[ s_k ])
                    if n > 0:
                        any_stats = True
                        cnv_stats[ s_k ] = sum(cnvstatistics[ s_k ]) / n
                        if cnv_stats[ s_k ] < 1:
                            cnv_stats[ s_k ] = round( cnv_stats[ s_k ], 3)
                        else:
                            cnv_stats[ s_k ] = int( cnv_stats[ s_k ] )
            else:
                no_cs_no += 1

            if not any_stats:
                no_stats_no += 1

            update_obj = { "info.callset_ids": cs_ids, "info.cnvstatistics": cnv_stats }

            """
            --- other biosample modification code
            """

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

            ####################################################################

            if not byc["args"].test:
                bios_coll.update_one( { "_id": s["_id"] }, { '$set': update_obj }  )
                bar.next()

        if not byc["args"].test:
            bar.finish()

        print("{} {} biosamples had no callsets".format(no_cs_no, ds_id))
        print("{} {} biosamples received no CNV statistics".format(no_stats_no, ds_id))         

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
################################################################################
################################################################################


if __name__ == '__main__':
    main()
