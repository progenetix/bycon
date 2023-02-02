import cgi, cgitb
import re, yaml
from pymongo import MongoClient

from cgi_parsing import *

################################################################################

def parse_filters(byc):

    if "filters" in byc["form_data"]:
        fs = byc["form_data"]["filters"]
        fs = check_filter_values(fs, byc)
        if len(fs) > 0:
            byc.update( { "filters": fs } )
            return byc
            
    return byc

################################################################################

def get_filter_flags(byc):

    ff = {
        "logic": byc[ "config" ][ "filter_flags" ][ "logic" ],
        "precision": byc[ "config" ][ "filter_flags" ][ "precision" ],
        "descendants": byc[ "config" ][ "filter_flags" ][ "include_descendant_terms" ]
    }

    if "form_data" in byc:
        if "filter_logic" in byc[ "form_data" ]:
            ff["logic"] = boolean_to_mongo_logic( byc["form_data"]['filter_logic'] )
        if "filter_precision" in byc[ "form_data" ]:
            ff["precision"] = byc["form_data"]['filter_precision']
        if "include_descendant_terms" in byc[ "form_data" ]:
            i_d_t = str(byc[ "form_data" ].get("include_descendant_terms", 1)).lower()
            if i_d_t in ["0", "-1", "no", "false"]:
                ff["descendants"] = False

    byc.update( { "filter_flags": ff } )

    return byc

################################################################################

def check_filter_values(filters, byc):

    f_defs = byc["filter_definitions"]

    checked = [ ]
    for f in filters:
        if not isinstance(f, dict):
            f = {"id":f}
        if not "id" in f:
            continue
        pre = re.split('-|:', f["id"])[0]
        for f_t, f_d in f_defs.items():
            if re.compile( f_d["pattern"] ).match( f["id"] ):       
                if f not in checked:
                    checked.append( f )

    return checked
  
################################################################################

def select_dataset_ids(byc):

    p_id = rest_path_value("datasets")
    if p_id:
        ds_id = p_id
        if ds_id in byc["dataset_definitions"].keys():
            byc.update( { "dataset_ids": [ ds_id ] } )
            return byc

    # accessid overrides ... ?
    if "accessid" in byc["form_data"]:
        accessid = byc["form_data"]["accessid"]

        ho_client = MongoClient()
        ho_db = ho_client[ byc["config"]["info_db"] ]
        ho_coll = ho_db[ byc["config"][ "handover_coll" ] ]
        h_o = ho_coll.find_one( { "id": accessid } )
        # TODO: catch error for mismatch
        if h_o:
            if "source_db" in h_o:
                ds_id = h_o["source_db"]
                if ds_id in byc["dataset_definitions"].keys():
                    byc.update( { "dataset_ids": [ ds_id ] } )
                    return byc            

    ds_ids = [ ]
    form = byc["form_data"]
    if "dataset_ids" in form:
        for ds_id in form["dataset_ids"]:
            if ds_id in byc["dataset_definitions"].keys():
                ds_ids.append(ds_id)
        if len(ds_ids) > 0:
            byc.update( { "dataset_ids": ds_ids } )
    
    return byc
  
################################################################################
