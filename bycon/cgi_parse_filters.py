import cgi, cgitb
import re, yaml
from os import path as path

################################################################################

def read_filter_definitions( **byc ):

    filter_defs = {}
    for ff in [ "filters", "custom_filters" ]:
        with open( path.join(path.abspath(byc[ "config" ][ "paths" ][ "module_root" ]), "config", ff+".yaml") ) as fd:
            defs = yaml.load( fd , Loader=yaml.FullLoader)
            for fpre in defs:
                filter_defs[fpre] = defs[fpre]
    
    return filter_defs

################################################################################

def parse_filters( **byc ):

    filters = byc["form_data"].getlist('filters')
    filters = ','.join(filters)
    filters = filters.split(',')

    # for debugging
    for opt, arg in byc["opts"]:
        if opt in ("-t"):
            filters = byc["service_info"][ "sampleAlleleRequests" ][0][ "filters" ]

    return(filters)
  
################################################################################

def get_dataset_ids( **byc ):

    dataset_ids = byc[ "form_data" ].getlist('datasetIds')
    dataset_ids = ','.join(dataset_ids)
    dataset_ids = dataset_ids.split(',')

    # for debugging
    for opt, arg in byc["opts"]:
        if opt in ("-t"):
            dataset_ids = byc["service_info"][ "sampleAlleleRequests" ][0][ "datasetIds" ]
    
    return(dataset_ids)
  
################################################################################

def create_queries_from_filters( **byc ):
        
    queries = { }
    query_lists = { }
    for coll_name in byc[ "config" ][ "collections" ]:
        query_lists[coll_name] = [ ]
 
    for filterv in byc[ "filters" ]:
        pref = re.split('-|:', filterv)[0]
       
        if pref in byc["filter_defs"]:
            if re.compile( byc["filter_defs"][pref]["pattern"] ).match(filterv):
                for scope in byc["filter_defs"][pref]["scopes"]:
                    m_scope = byc["filter_defs"][pref]["scopes"][scope]
                    if m_scope["default"]:
                        query_lists[ scope ].append( { m_scope[ "db_key" ]: { "$regex": "^"+filterv } } )
                        break

    for coll_name in byc[ "config" ][ "collections" ]:
        if len(query_lists[coll_name]) == 1:
            queries[ coll_name ] = query_lists[coll_name][0]
        elif len(query_lists[coll_name]) > 1:
            queries[ coll_name ] = { "$and": query_lists[coll_name] }
    return queries

################################################################################

def cgi_exit_on_error(shout):
    print("Content-Type: text")
    print()
    print(shout)
    exit()

