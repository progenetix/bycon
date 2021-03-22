import json
from pymongo import MongoClient
from bson.objectid import ObjectId

from cgi_utils import *

################################################################################

def retrieve_variants(ds_id, r, byc):

    vs = [ ]

    mongo_client = MongoClient()
    v_coll = mongo_client[ ds_id ][ "variants" ]
    bs_coll = mongo_client[ ds_id ][ "biosamples" ]

    if not byc["method"] in byc["these_prefs"]["all_variants_methods"]:
        if "vs._id" in byc["query_results"]:
            for v in v_coll.find({"_id": { "$in": byc["query_results"]["vs._id"]["target_values"] } }):
                vs.append(v)
            return vs
        else:
            return vs

    ############################################################################

    for bs_id in byc["query_results"]["bs.id"][ "target_values" ]:
        for v in v_coll.find(
                {"biosample_id": bs_id },
                { "_id": 0, "assembly_id": 0, "digest": 0, "callset_id": 0 }
        ):
            v["log2"] = False
            if "info" in v:
                if "cnv_value" in v["info"]:
                    if isinstance(v["info"]["cnv_value"],float):
                        v["log2"] = round(v["info"]["cnv_value"], 3)
            v["start"] = int(v["start"])
            v["end"] = int(v["end"])
            if v["log2"] == False:
                del(v["log2"])
            if "info" in v:
                del(v["info"])
            vs.append(v)

    return vs

################################################################################

def create_pgxseg_header(ds_id, r, byc):

    p_h = []

    mongo_client = MongoClient()
    bs_coll = mongo_client[ ds_id ][ "biosamples" ]

    if not "pgxseg" in byc["method"]:
        return p_h

    for d in ["id", "assemblyId"]:
        p_h.append("#meta=>{}={}".format(d, byc["dataset_definitions"][ds_id][d]))
    for m in ["variant_count", "biosample_count"]:
        p_h.append("#meta=>{}={}".format(m, r["response"]["info"][m]))
    if "filters" in r["meta"]["received_request"]:
        p_h.append("#meta=>filters="+','.join(r["meta"]["received_request"]["filters"]))

    for bs_id in byc["query_results"]["bs.id"][ "target_values" ]:
        bs = bs_coll.find_one( { "id": bs_id } )
        h_line = "#sample=>sample_id={}".format(bs_id)
        for b_c in bs[ "biocharacteristics" ]:
            if "NCIT:C" in b_c["id"]:
                h_line = '{};group_id={};group_label={};NCIT::id={};NCIT::label={}'.format(h_line, b_c["id"], b_c["label"], b_c["id"], b_c["label"])
        p_h.append(h_line)
    p_h.append("{}\t{}\t{}\t{}\t{}\t{}".format("biosample_id", "reference_name", "start", "end", "log2", "variant_type" ) )

    return p_h

################################################################################

def print_variants_json(vs):

    l_i = len(vs) - 1
    for i,v in enumerate(vs):
        if i == l_i:
            print(json.dumps(v, indent=None, sort_keys=False, default=str, separators=(',', ':')))
        else:
            print(json.dumps(v, indent=None, sort_keys=False, default=str, separators=(',', ':')), end = ',')

################################################################################

def export_variants_download(vs, r, byc):

    open_json_streaming(r, "variants.json")
    print_variants_json(vs)
    close_json_streaming()

################################################################################

def print_variants_pgxseg(vs):

    for v in vs:
        if not "log2" in v:
            v["log2"] = "."
        print("{}\t{}\t{}\t{}\t{}\t{}".format(v["biosample_id"], v["reference_name"], v["start"], v["end"], v["log2"], v["variant_type"]) )

################################################################################

def export_pgxseg_download(ds_id, r, vs, byc):

    p_h = create_pgxseg_header(ds_id, r, byc)

    open_text_streaming()
    for h_l in p_h:
        print(h_l)
    print_variants_pgxseg(vs)
    close_text_streaming()

################################################################################
