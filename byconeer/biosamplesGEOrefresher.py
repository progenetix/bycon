#!/usr/local/bin/python3

import re, json, yaml
from os import path, environ, pardir, mkdir
import sys, datetime
from isodate import date_isoformat
from pymongo import MongoClient
import argparse
import statistics
from progress.bar import Bar
import requests


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
    parser.add_argument("-f", "--filters", help="prefixed filter value for ext. identifier")
    # parser.add_argument("-t", "--test", help="test setting")
    parser.add_argument('-i', '--inputfile', help='a custom file to specify input data')
    parser.add_argument('-s', '--scopes', help='scopes, e.g. "stage", comma-separated')
    byc.update({ "args": parser.parse_args() })

    return byc

################################################################################

def main():

    biosamples_refresher()

################################################################################

def biosamples_refresher():

    # TODO: Clean solution?

    byc = initialize_service()
    _get_args(byc)

    if not byc["args"].scopes:
        print( "You have to provide at least one of the scopes in `-s {}`".format(",".join(supported_scopes)))
        exit()

    s_scopes = byc["this_config"]["text_processing_scopes"]
    sel_scopes = []

    for scope in re.split(",", byc["args"].scopes):
        if scope in s_scopes.keys():
            sel_scopes.append(scope)
        else:
            print("{} is not a supported scope".format(scope))

    byc["dataset_ids"] = ["progenetix"]

    parse_filters(byc)
    parse_variants(byc)
    initialize_beacon_queries(byc)
    generate_genomic_intervals(byc)

    print("Running progenetix ...")

    no_cs_no = 0
    no_stats_no = 0
    ds_id = byc["dataset_ids"][0]
    id_filter = "GSM"

    if byc["args"].filters:
        id_filter = byc["args"].filters

    bios_query = { "$or": [
        { "external_references.id": { "$regex": id_filter } },
        { "info.legacy_id": { "$regex": id_filter } }
    ] }

    data_client = MongoClient( )
    data_db = data_client[ ds_id ]
    bios_coll = data_db[ "biosamples" ]
    cs_coll = data_db[ "callsets" ]

    bs_ids = []

    for bs in bios_coll.find (bios_query, {"id":1 } ):
        bs_ids.append(bs["id"])

    no =  len(bs_ids)

    bar = Bar("{} {} samples".format(no, ds_id), max = no, suffix='%(percent)d%%'+" of "+str(no) )

    series_re = re.compile(r'^.*?(GSE\d+?)(:?[^\d]|$)', re.IGNORECASE)
    experiment_re = re.compile(r'^.*?(GSM\d+?)(:?[^\d]|$)', re.IGNORECASE)
    platform_re = re.compile(r'^.*?(GPL\d+?)(:?[^\d]|$)', re.IGNORECASE)

    missing_ids = []
    coll_lines = []
    coll_objs = []

    header = ["id", "analysis_info.experiment_id", "analysis_info.series_id", "analysis_info.platform_id"]
    for scp in sel_scopes:
        header.append(s_scopes[scp]["db_key"])
        header.append("_old_"+scp)
        header.append("_input_"+scp)
        header.append("_note_"+scp)

    coll_lines.append("\t".join(header))

    for bsid in bs_ids:

        get_geosoft = True
        gsm = ""
        gse = ""
        gpl = ""
        gsm_soft = False

        # TODO: Read in files if existing ... 
        # To be added after some collection exists

        s = bios_coll.find_one({ "id":bsid })

        e_r_s = s.get("external_references", [])
        for e_r in e_r_s:
            if "GSM" in e_r["id"]:
                gsm = experiment_re.match(e_r["id"]).group(1)
            if "GSE" in e_r["id"]:
                gse = series_re.match(e_r["id"]).group(1)
            if "GPL" in e_r["id"]:
                gpl = platform_re.match(e_r["id"]).group(1)

        if len(gse) < 5 or len(gsm) < 5:

            # print("\n{} did not have GEO ids in external_references!!".format(bsid))
            missing_ids.append("\t".join([bsid, gse, gsm, gpl]))
            bar.next()
            continue

        gsm_soft = _read_retrieve_save_gsm_soft(pkg_path, gsm, gse, byc)

        if not gsm_soft:
            print("\n!!!! No soft file for {}".format(gsm))
            bar.next()
            continue

        _filter_gsm_soft(gsm_soft)

        updating_scopes = False

        line_coll = {}
        for h_i in header:
            line_coll.update({h_i:""})
        line_coll.update({
            "id": bsid,
            "analysis_info.experiment_id": gsm,
            "analysis_info.series_id": gse,
            "analysis_info.platform_id": gpl
        })

        new_info = s["info"].copy()

        sample_characteristics = geosoft_preclean_sample_characteristics(gsm_soft, byc)

        for scp in sel_scopes:

            line_coll.update({"_old_"+scp: s["info"].get(s_scopes[scp]["info_parameter"], "")})
            # scope_update_f = "geosoft_extract_tumor_"+scp
            # globals()[scope_update_f](sample_characteristics, line_coll, s_scopes[scp], byc)
            geosoft_extract_geo_meta(sample_characteristics, line_coll, s_scopes[scp], byc)
            if len(line_coll[s_scopes[scp]["db_key"]]) > 0 or len(line_coll["_note_"+scp]) > 0:
                new_info.update({scope:line_coll[s_scopes[scp]["db_key"]]})
                updating_scopes = True

        coll_line = ""
        if updating_scopes:
            line = []
            for h_k in header:
                line.append(line_coll.get(h_k, ""))
            coll_line = "\t".join(line)
            coll_lines.append(coll_line)
            coll_objs.append(line_coll)
            bar.next()
        else:
            bar.next()
            continue

        # TODO: make sure the DB update is being handled by dedicated script
        #     update_obj = {
        #         "analysis_info": {
        #             "experiment_id": gsm,
        #             "platform_id": geosoft_extract_gpl(gsm_soft, platform_re),
        #             "series_id": gse
        #         },
        #         "info": new_info
        #     }
        #     print("\nupdating {}".format(s["id"]))
        #     bios_coll.update_one( { "_id": s["_id"] }, { '$set': update_obj }  )
        #     bar.next()

    bar.finish()

    tmp_path = _save_tmp_file("gsm-metadata_"+"_".join(sel_scopes)+".tsv", coll_lines, byc)
    print("=> Wrote {}".format(tmp_path))
    print("=> metadata for {} samples".format(len(coll_lines) - 1))

    for scp in sel_scopes:
        scp_dists = {}
        for c in coll_objs:
            if len(c[ s_scopes[scp]["db_key"] ]) > 0:
                scp_dists.update({ c[ s_scopes[scp]["db_key"] ] :1})
        print("=> Values in scope \"{}\":\n{}".format(s_scopes[scp]["id"], "\n".join(list(scp_dists.keys()))))



################################################################################

def _read_retrieve_save_gsm_soft(pkg_path, gsm, gse, byc):

    gse_path = path.join( pkg_path, *byc["config"]["paths"]["geosoft_file_root"], gse )
    gsm_path = path.join( gse_path, gsm+".txt" )

    if path.isfile(gsm_path):               
        gsm_soft = open(gsm_path).read().splitlines()
        return gsm_soft
    else:
        gsm_soft = retrieve_geosoft_file(gsm, byc)
        if not path.isdir(gse_path):
            mkdir(gse_path)
        s_f = open(gsm_path, 'w')
        for l in gsm_soft:
            s_f.write(l)
        s_f.close()
        return gsm_soft

    return False

################################################################################

def _filter_gsm_soft(gsm_soft):

    # getting rid of data header and some verbose stuff
    gsm_soft = list(filter(lambda x:'Sample_' in x, gsm_soft))
    gsm_soft = list(filter(lambda x:'_protocol' not in x, gsm_soft))
    
    return gsm_soft

################################################################################

def _save_tmp_file(filename, content, byc):

    f_p = path.join( pkg_path, *byc["config"]["paths"]["tmp_file_root"], filename )
    t_f = open(f_p, 'w')
    for l in content:
        t_f.write(l+"\n")
    t_f.close()

    return f_p

################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    main()
