import cgi, cgitb
import re, yaml
from os import path as path

################################################################################

def read_filter_definitions( **paths ):

    filter_defs = {}
    for ff in [ "filters", "custom_filters" ]:
        with open( path.join(path.abspath(paths[ "module_root" ]), "config", ff+".yaml") ) as fd:
            defs = yaml.load( fd , Loader=yaml.FullLoader)
            for fpre in defs:
                filter_defs[fpre] = defs[fpre]
    
    return filter_defs

################################################################################

def parse_filters( **byc ):

    if "form_data" in byc:
        if len(byc["form_data"]) > 0:
            filters = byc["form_data"].getlist('filters')
            filters = ','.join(filters)
            filters = filters.split(',')
            filters = _check_filter_values(filters, byc["filter_defs"])
            return(filters)
    

    if "rest_pars" in byc:
        if "filters" in byc["rest_pars"]:
            filters = byc["rest_pars"][ "filters" ].split(',')
            filters = _check_filter_values(filters, byc["filter_defs"])
            return(filters)
    
    # for debugging
    if "args" in byc:
        if byc["args"].filters:
            filters = byc["args"].filters.split(',')
            filters = _check_filter_values(filters, byc["filter_defs"])
            return(filters)
    
    # for debugging
        if byc["args"].test:
            filters = byc["service_info"][ "sampleAlleleRequests" ][0][ "filters" ]
            filters = _check_filter_values(filters, byc["filter_defs"])
            return(filters)
    
    return([])

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

    dataset_ids = byc[ "form_data" ].getlist('datasetIds')
    dataset_ids = ','.join(dataset_ids)
    dataset_ids = dataset_ids.split(',')

    if "datasetIds" in byc["rest_pars"]:
        dataset_ids = byc["rest_pars"][ "datasetIds" ].split(',')
        return(dataset_ids)

    # for debugging
    if byc["args"].test:
        dataset_ids = byc["service_info"][ "sampleAlleleRequests" ][0][ "datasetIds" ]
    
    return(dataset_ids)
  

################################################################################

def cgi_exit_on_error(shout):
    print("Content-Type: text")
    print()
    print(shout)
    exit()

