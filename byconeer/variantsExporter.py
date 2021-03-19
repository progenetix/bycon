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
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from bycon.lib.read_specs import *
from bycon.lib.parse_filters import *
from bycon.lib.query_execution import execute_bycon_queries
from bycon.lib.query_generation import generate_queries

service_lib_path = path.join( pkg_path, "services", "lib" )
sys.path.append( service_lib_path )

from service_utils import initialize_service

"""
## `variantsExporter`

* variantsExporter.py -f "icdot-C71.6" -d progenetix -o ~/Downloads/test.pgxseg
"""

################################################################################
################################################################################
################################################################################

def _get_args(byc):

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datasetids", help="dataset")
    parser.add_argument("-o", "--outfile", help="output file")
    parser.add_argument("-f", "--filters", help="prefixed filter values, comma concatenated")
    parser.add_argument("--value-only", dest='value_only', action='store_true', help="only output variants with values")
    parser.set_defaults(value_only=False)
    byc.update({ "args": parser.parse_args() })

    return byc

################################################################################

def main():

    variants_exporter()

################################################################################

def variants_exporter():

    byc = initialize_service()
    _get_args(byc)

    select_dataset_ids(byc)
    check_dataset_ids(byc)

    if len(byc["dataset_ids"]) < 1:
        print("No existing dataset was provided with -d ...")
        exit()

    ds_id = byc[ "dataset_ids" ][ 0 ]

    get_filter_flags(byc)  
    parse_filters(byc)
    generate_queries(byc)
    execute_bycon_queries( ds_id, byc )

    all_bs_no = byc["query_results"]["bs.id"]["target_count"]
    mongo_client = MongoClient( )
    vs_coll = mongo_client[ ds_id ][ "variants" ]
    bs_coll = mongo_client[ ds_id ][ "biosamples" ]

    bar = Bar("Testing {} {} samples".format(all_bs_no, ds_id), max = all_bs_no, suffix='%(percent)d%%' )

    used_bs_ids = set()
    all_v_no = 0
    for bs_id in byc["query_results"]["bs.id"]["target_values"]:
        for v in vs_coll.find({ "biosample_id": bs_id }):
            all_v_no += 1
            val = ""
            if "info" in v:
                if "cnv_value" in v["info"]:
                    if isinstance(v["info"]["cnv_value"],float):
                        val = v["info"]["cnv_value"]
            break
        if (not byc["args"].value_only) or (val != ""):
            used_bs_ids.add(bs_id)
        bar.next()
    bar.finish()

    used_bs_no = len(used_bs_ids)

    print("=> Writing header data for {} samples with variants...".format(used_bs_no))

    f = open(byc["args"].outfile, "w")

    for bs_id in used_bs_ids:
        bs = mongo_client[ ds_id ][ "biosamples" ].find_one( { "id": bs_id } )
        h_line = "# sample_id={}".format(bs_id)
        for b_c in bs[ "biocharacteristics" ]:
            if "NCIT:C" in b_c["id"]:
                h_line = '{};group_id={};group_label={};NCIT::id={};NCIT::label={}'.format(h_line, b_c["id"], b_c["label"], b_c["id"], b_c["label"])
        f.write(h_line+"\n")

    bar = Bar("Variants from {} {} samples".format(used_bs_no, ds_id), max = used_bs_no, suffix='%(percent)d%%' )

    used_v_no = 0
    for bs_id in used_bs_ids:
        for v in vs_coll.find({ "biosample_id": bs_id }):
            val = ""
            if "info" in v:
                if "cnv_value" in v["info"]:
                    if isinstance(v["info"]["cnv_value"],float):
                        val = v["info"]["cnv_value"]
            if (not byc["args"].value_only) or (val != ""):
                used_v_no +=1
                f.write("{}\t{}\t{}\t{}\t{}\t{}\n".format(bs_id, v["reference_name"], int(v["start"]), int(v["end"]), v["variant_type"], '{:.4f}'.format(val)) )

        bar.next()
    bar.finish()

    f.close()

    print("{} variants from {} biosamples were written to {}".format(used_v_no, len(used_bs_ids) ,byc["args"].outfile) )

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
