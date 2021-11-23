import cgi, cgitb
import re, yaml
from pymongo import MongoClient

from cgi_parse import *

################################################################################

def parse_filters(byc):

    byc.update({"filters":[]})

    if "form_data" in byc:
        if "filters" in byc["form_data"]:
            fs = byc["form_data"]["filters"]
            fs = _check_filter_values(fs, byc["filter_definitions"])
            if len(fs) > 0:
                byc.update( { "filters": fs } )
                return byc
    
    if "args" in byc:
        if byc["args"].filters:
            f = byc["args"].filters.split(',')
            fs = _check_filter_values(f, byc["filter_definitions"])
            if len(fs) > 0:
                byc.update( { "filters": fs } )
                return byc
        
    return byc

################################################################################

def get_filter_flags(byc):

    ff = {
        "logic": byc[ "config" ][ "filter_flags" ][ "logic" ],
        "precision": byc[ "config" ][ "filter_flags" ][ "precision" ]
    }

    if "form_data" in byc:
        if "filterLogic" in byc[ "form_data" ]:
            l = byc["form_data"]['filterLogic']
            if "OR" in l:
                ff["logic"] = '$or'
            if "AND" in l:
                ff["logic"] = '$and'
        if "filterPrecision" in byc[ "form_data" ]:
            ff["precision"] = byc["form_data"]['filterPrecision']

    byc.update( { "filter_flags": ff } )

    return byc

################################################################################

def _check_filter_values(filters, filter_defs):

    checked = [ ]
    for f in filters:
        if not isinstance(f, dict):
            f = {"id":f}
        if not "id" in f:
            continue
        pre = re.split('-|:', f["id"])[0]
        if pre in filter_defs:
            if re.compile( filter_defs[ pre ]["pattern"] ).match( f["id"] ):
                checked.append( f )

    return checked
  
################################################################################

def select_dataset_ids(byc):

    # different var name & return if provided

    ds_ids = [ ]

    p_id = rest_path_value("datasets")

    if p_id:
        if not "empty_value" in p_id:
            for ds_id, ds in byc[ "dataset_definitions" ].items():
                if p_id == ds_id:
                    byc.update( { "dataset_ids": [ds_id] } )
                    return byc

    if "form_data" in byc:

        # TODO: deparsing the different request object formats shouldn't ne 
        # necessarily here...
        if "datasets" in byc["form_data"]:
            if "datasetIds" in byc["form_data"]["datasets"]:
                ds_ids = byc["form_data"]["datasets"]["datasetIds"]
        elif "datasetIds" in byc["form_data"]:
            ds_ids = byc["form_data"]["datasetIds"]

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
                    ds_ids = [ h_o["source_db"] ]
                    

    if len(ds_ids) > 0:
        byc.update( { "dataset_ids": ds_ids } )
        return byc

    if "args" in byc:
        try:
            if byc["args"].alldatasets:
                byc.update( { "dataset_ids": byc["config"][ "dataset_ids" ] } )
                return byc
        except AttributeError:
            pass
        try:
            if byc["args"].datasetids:
                ds_ids = byc["args"].datasetids.split(",")
                if ds_ids[0] in byc["config"][ "dataset_ids" ]:
                    byc.update( { "dataset_ids": ds_ids } )
                    return byc
        except AttributeError:
            pass
    
    return byc
  
################################################################################

def check_dataset_ids(byc):

    dataset_ids = [ ]

    if not "dataset_ids" in byc:
        byc.update( { "dataset_ids": [ ] } )


    if len(byc["dataset_ids"]) < 1:
        if "dataset_default" in byc["config"]:
            byc["dataset_ids"].append(byc["config"]["dataset_default"])

    for ds in byc["dataset_ids"]:
        if ds in byc["dataset_definitions"].keys():
            dataset_ids.append(ds)

    byc.update( { "dataset_ids": dataset_ids } )

    return byc

################################################################################


