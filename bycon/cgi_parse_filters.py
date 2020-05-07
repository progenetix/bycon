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

    if "form_data" in byc:
        filters = byc["form_data"].getlist('filters')
        filters = ','.join(filters)
        filters = filters.split(',')
        return(filters)

     # for debugging
    if byc["args"].filters:
        filters = byc["args"].filters.split(',')
        return(filters)

    # for debugging
    if byc["args"].test:
        filters = byc["service_info"][ "sampleAlleleRequests" ][0][ "filters" ]
        return(filters)

    return([])
  
################################################################################

def get_dataset_ids( **byc ):

    dataset_ids = byc[ "form_data" ].getlist('datasetIds')
    dataset_ids = ','.join(dataset_ids)
    dataset_ids = dataset_ids.split(',')

    # for debugging
    if byc["args"].test:
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
            pref_defs = byc["filter_defs"][pref]
            if re.compile( pref_defs["pattern"] ).match(filterv):
                for scope in pref_defs["scopes"]:
                    m_scope = pref_defs["scopes"][scope]
                    if m_scope["default"]:
                        query_lists[ scope ].append( { pref_defs[ "db_key" ]: { "$regex": "^"+filterv } } )
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

