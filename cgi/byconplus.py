#!/usr/local/bin/python3

import cgi, cgitb
import json, yaml
from bson.json_util import dumps
from os import path as path
import sys

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *

################################################################################
################################################################################
################################################################################

cgitb.enable()  # for debugging

################################################################################

def main():

    print('Content-Type: text')
    print()

    with open( path.join( path.abspath( dir_path ), '..', "config", "defaults.yaml" ) ) as cf:
        config = yaml.full_load( cf )
    config[ "paths" ][ "out" ] = path.abspath( config[ "paths" ][ "web_temp_dir_abs" ] )
    
    form_data = cgi_parse_query()
    filters = parse_filters(form_data)
    filter_defs = read_filter_definitions(dir_path)
    
    kwargs = { "config": config, "filter_defs": filter_defs, "filters": filters }
    queries = create_queries_from_filters(**kwargs)

    if not queries:
        cgi_exit_on_error('No query specified; please use "-h" for examples')

    kwargs = { "config": config, "queries": queries }
    query_results = execute_bycon_queries(**kwargs)
    
    print(dumps(filters))
    print(dumps(queries))
    print(dumps(query_results))
    
################################################################################
################################################################################

if __name__ == '__main__':
    main()
