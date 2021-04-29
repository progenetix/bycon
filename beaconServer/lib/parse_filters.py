import cgi, cgitb
import re, yaml
from pymongo import MongoClient

from cgi_utils import *

################################################################################

def parse_filters(byc):

    byc.update({"filters":[]})

    if "form_data" in byc:
        f = form_return_listvalue( byc["form_data"], "filters" )
        f = _check_filter_values(f, byc["filter_definitions"])
        if len(f) > 0:
            byc.update( { "filters": f } )
            return byc
    
    if "args" in byc:
        if byc["args"].filters:
            f = byc["args"].filters.split(',')
            f = _check_filter_values(f, byc["filter_definitions"])
            if len(f) > 0:
                byc.update( { "filters": f } )
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
            l = byc["form_data"].getvalue('filterLogic')
            if "OR" in l:
                ff["logic"] = '$or'
            if "AND" in l:
                ff["logic"] = '$and'
        if "filterPrecision" in byc[ "form_data" ]:
            ff["precision"] = byc["form_data"].getvalue('filterPrecision')

    # command line / legacy
    if "exact_match" in byc:
        ff["precision"] = "exact"

    byc.update( { "filter_flags": ff } )

    return byc

################################################################################

def _check_filter_values(filters, filter_defs):

    checked = [ ]
    for f in filters:
        pre = re.split('-|:', f)[0]
        if pre in filter_defs:
            if re.compile( filter_defs[ pre ]["pattern"] ).match( f ):
                checked.append( f )

    return checked
  
################################################################################

def select_dataset_ids(byc):

    # different var name & return if provided

    ds_ids = [ ]

    if "form_data" in byc:
        if "datasetIds" in byc["form_data"]:
            ds_ids = form_return_listvalue( byc["form_data"], "datasetIds" )

        # accessid overrides ... ?
        if "accessid" in byc["form_data"]:
            accessid = byc["form_data"].getvalue("accessid")
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


