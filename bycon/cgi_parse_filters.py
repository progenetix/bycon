import cgi, cgitb
import re, yaml
from os import path as path

################################################################################

def read_filter_definitions(dir_path):

    filter_defs = {}
    for ff in [ "filters", "custom_filters" ]:
        with open( path.join(path.abspath(dir_path), "..", "config", ff+".yaml") ) as fd:
            defs = yaml.load( fd , Loader=yaml.FullLoader)
            for fpre in defs:
                filter_defs[fpre] = defs[fpre]
    
    return filter_defs

################################################################################

def parse_filters(form_data):

    filters = form_data.getlist('filters')
    filters = ','.join(filters)
    filters = filters.split(',')
    
    return(filters)
  
################################################################################

def get_dataset_ids(form_data):

    dataset_ids = form_data.getlist('datasetIds')
    dataset_ids = ','.join(dataset_ids)
    dataset_ids = dataset_ids.split(',')
    
    return(dataset_ids)
  
################################################################################

def create_queries_from_filters(**kwargs):
        
    queries = { }
    query_lists = { }
    for coll_name in kwargs[ "config" ][ "collections" ]:
        query_lists[coll_name] = [ ]
 
    for filterv in kwargs[ "filters" ]:
        pref = re.split('-|:', filterv)[0]
        
        if pref in kwargs["filter_defs"]:
            if re.compile( kwargs["filter_defs"][pref]["pattern"] ).match(filterv):
                for scope in kwargs["filter_defs"][pref]["scopes"]:
                    m_scope = kwargs["filter_defs"][pref]["scopes"][scope]
                    if m_scope["default"]:
                        query_lists[ scope ].append( { m_scope[ "db_key" ]: { "$regex": "^"+filterv } } )

    for coll_name in kwargs[ "config" ][ "collections" ]:
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

