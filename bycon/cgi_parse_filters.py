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

def get_dataset_ids( **byc ):

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

def create_queries_from_filters( **byc ):

    """podmd

    #### `create_queries_from_filters`

    This method creates a query object (dictionary) with entries for each of the
    standard data collections.

    Filter values are not checked for their correct syntax; this should have
    happened in a pre-parsing step and allows to use the method with non-standard
    values, e.g. to fix erroneous database entries.

    ###### Options

    * `exact_match` creates query items with exact (string) matches, in contrast
    to the standard teatment of query terms as start-anchored partial matches
    * `mongostring` leads to creation of MongoDB compatible query strings
    instead of `pymongo` objects (i.e. the result is to be used in `mongo`
    commands)

    podmd"""
        
    queries = { }
    query_lists = { }
    for coll_name in byc[ "config" ][ "collections" ]:
        query_lists[coll_name] = [ ]
 
    for filterv in byc[ "filters" ]:
        pre = re.split('-|:', filterv)[0]
        if pre in byc["filter_defs"]:
            pre_defs = byc["filter_defs"][pre]
            for scope in pre_defs["scopes"]:
                m_scope = pre_defs["scopes"][scope]
                if m_scope["default"]:
                    if "exact_match" in byc:
                        if "mongostring" in byc:
                            query_lists[ scope ].append( '{ "'+pre_defs[ "db_key" ]+'": "'+filterv+'" }' )
                        else:
                            query_lists[ scope ].append( { pre_defs[ "db_key" ]: filterv } )
                        break
                    else:
                        if "mongostring" in byc:
                            filterv = re.sub(':', '\:', filterv)
                            filterv = re.sub('-', '\-', filterv)
                            query_lists[ scope ].append( '{ "'+pre_defs[ "db_key" ]+'": { $regex: /^'+filterv+'/ } }' )
                        else:
                            query_lists[ scope ].append( { pre_defs[ "db_key" ]: { "$regex": "^"+filterv } } )
                        break

    for coll_name in byc[ "config" ][ "collections" ]:
        if len(query_lists[coll_name]) == 1:
            queries[ coll_name ] = query_lists[coll_name][0]
        elif len(query_lists[coll_name]) > 1:
            if "mongostring" in byc:
                queries[ coll_name ] = '{ $and: [ '+','.join(query_lists[coll_name])+' ] }'
            else:
                queries[ coll_name ] = { "$and": query_lists[coll_name] }

    return queries

################################################################################

def cgi_exit_on_error(shout):
    print("Content-Type: text")
    print()
    print(shout)
    exit()

