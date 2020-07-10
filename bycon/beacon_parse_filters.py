import cgi, cgitb
import re, yaml

################################################################################

def parse_filters( **byc ):

    filters = [ ]
    if "form_data" in byc:
        if len(byc["form_data"]) > 0:
            filters = byc["form_data"].getlist('filters')
            filters = ','.join(filters)
            filters = filters.split(',')
            filters = _check_filter_values(filters, byc["filter_defs"])
            return filters

    # TODO: purge the rest_pars vars...
    # if "rest_pars" in byc:
    #     if "filters" in byc["rest_pars"]:
    #         filters = byc["rest_pars"][ "filters" ].split(',')
    #         filters = _check_filter_values(filters, byc["filter_defs"])
    #         return(filters)
    
    # for debugging
    if "args" in byc:
        if byc["args"].filters:
            filters = byc["args"].filters.split(',')
            filters = _check_filter_values(filters, byc["filter_defs"])
            return filters
    
    # for debugging
        if byc["args"].test:
            filters = byc["service_info"][ "sampleAlleleRequests" ][0][ "filters" ]
            filters = _check_filter_values(filters, byc["filter_defs"])
            return filters
    
    return filters

################################################################################

def _check_filter_values(filters, filter_defs):

    checked = [ ]
    for f in filters:
        pre = re.split('-|:', f)[0]
        if pre in filter_defs:
            if re.compile( filter_defs[ pre ]["pattern"] ).match( f ):
                checked.append( f )

    return(checked)
  
################################################################################

def select_dataset_ids( **byc ):

    ds_ids = byc[ "form_data" ].getlist('datasetIds')
    ds_ids = ','.join(ds_ids)
    ds_ids = ds_ids.split(',')

    if "hoid" in byc["form_data"]:
        accessid = byc["form_data"].getvalue("accessid")
        h_o = ho_coll.find_one( { "id": accessid } )
        # TODO: catch error for mismatch
        ds_ids = [ h_o["source_db"] ]

    dataset_ids = [ ]
    for ds in ds_ids:
        if ds in byc["datasets_info"].keys():
            dataset_ids.append(ds)

    # for debugging
    if byc["args"].test:
        dataset_ids = byc["service_info"][ "sampleAlleleRequests" ][0][ "datasetIds" ]
    
    return dataset_ids
  
################################################################################

def cgi_exit_on_error(shout):

    print("Content-Type: text")
    print()
    print(shout)
    exit()

