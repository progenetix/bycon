import cgi, cgitb
import re, yaml
from pymongo import MongoClient

################################################################################

def parse_filters( **byc ):

    filters = [ ]

    # if existing, e.g. defaults
    if "filters" in byc:
        filters = byc["filters"]

    if "form_data" in byc:
        if len(byc["form_data"]) > 0:
            filters = byc["form_data"].getlist('filters')
            filters = ','.join(filters)
            filters = filters.split(',')
            filters = _check_filter_values(filters, byc["filter_defs"])
            return filters
    
    # for debugging
    if "args" in byc:
        if byc["args"].filters:
            filters = byc["args"].filters.split(',')
            filters = _check_filter_values(filters, byc["filter_defs"])
            return filters
    
        if byc["args"].test:
            filters = byc["service_info"][ "sampleAlleleRequests" ][0][ "filters" ]
            filters = _check_filter_values(filters, byc["filter_defs"])
            return filters
    
    return filters

################################################################################

def get_filter_flags( **byc ):

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

    return ff

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

def select_dataset_ids( **byc ):

    ds_ids = [ ]

    # if existing, e.g. defaults
    if "dataset_ids" in byc:
        ds_ids = byc["dataset_ids"]

    if "form_data" in byc:

        if "datasetIds" in byc["form_data"]:

            ds_ids = byc[ "form_data" ].getlist('datasetIds')
            ds_ids = ','.join(ds_ids)
            ds_ids = ds_ids.split(',')

        # accessid overrides ... ?
        if "accessid" in byc["form_data"]:
            accessid = byc["form_data"].getvalue("accessid")
            ho_client = MongoClient()
            ho_db = ho_client[ byc["config"]["info_db"] ]
            ho_coll = ho_db[ byc["config"][ "handover_coll" ] ]
            h_o = ho_coll.find_one( { "id": accessid } )
            # TODO: catch error for mismatch
            ds_ids = [ h_o["source_db"] ]

    # for debugging
    if "args" in byc:
        if byc["args"].test:
            ds_ids = byc["service_info"][ "sampleAlleleRequests" ][0][ "datasetIds" ]
    
    return ds_ids
  
################################################################################

def beacon_check_dataset_ids( **byc ):

    dataset_ids = [ ]
    for ds in byc["dataset_ids"]:
        if ds in byc["datasets_info"].keys():
            dataset_ids.append(ds)

    return dataset_ids

################################################################################

def cgi_exit_on_error(shout):

    print("Content-Type: text")
    print()
    print(shout)
    exit()

