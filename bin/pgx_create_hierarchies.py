#!/usr/local/bin/python3

import sys, yaml, re, json
from pymongo import MongoClient
from os import path as path
from ontobio.ontol_factory import OntologyFactory
from ontobio.assoc_factory import AssociationSetFactory
from networkx import nx


# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *

################################################################################
################################################################################
################################################################################

def main():

    """podmd

    This app creates codi hierarchies for the different disease code 
    representations of Progenetix data model biosamples.
    
    For existing external hierarchies, the original model is read in first and 
    then reduced to a version containing only classes where the class itself
    or at least one of its children has data in the respective dataset.
    
    #### NCIT Noplasm Core
    
    * NCIT Neoplasm OWL
        - <http://www.obofoundry.org/ontology/ncit.html>
    * JSON serialization of NCIT Neoplasm core
        - <http://purl.obolibrary.org/obo/ncit/neoplasm-core.owl>

    end_podmd"""

    with open( path.join( path.abspath( dir_path ), '..', "config", "defaults.yaml" ) ) as cf:
        config = yaml.load( cf , Loader=yaml.FullLoader)
    config[ "paths" ][ "module_root" ] = path.join( path.abspath( dir_path ), '..' )
    config[ "paths" ][ "out" ] = path.join( config[ "paths" ][ "module_root" ], "data", "out" )
    config[ "paths" ][ "mapping_file" ] = path.join( config[ "paths" ][ "module_root" ], "rsrc", "ncit", "neoplasm-core.json" )
    
    filter_defs = read_filter_definitions( **{ "config": config } )    

    
    # processing ncit
    # TODO: module, reading in the different hierarchies (ICDO-M, NCIt ...)
    prefix = "ncit"
    pre_filter = re.compile( filter_defs[ prefix ][ "pattern" ] )

    # TODO: module, run separately for defined datasets
    mongo_client = MongoClient()
    mongo_db = mongo_client[ "progenetix" ]
    mongo_coll = mongo_db[ "biosamples" ]
    onto_ids = mongo_coll.distinct( "biocharacteristics.type.id", { "biocharacteristics.type.id": { "$regex": pre_filter } } )
    onto_ids = list(filter(pre_filter.match, onto_ids))
    print(len(onto_ids))
        
    ONTO_IDs = list(map(str.upper, onto_ids))
    ONTO_IDs.append('NCIT:C3262')
    
    print("reading "+str(config[ "paths" ][ "mapping_file" ]))
    ont = OntologyFactory().create( config[ "paths" ][ "mapping_file" ] )
    
    [root] = ont.search('NCIT:C3262')
    all_ancestors = set( ONTO_IDs )
    
    for onto_id in ONTO_IDs:
        
        if onto_id == 'NCIT:C3262':
            continue
            
        [matched] = ont.search(onto_id)
        oldies = ont.ancestors(matched)
        oldies = set(filter(pre_filter.match, oldies))
        for old in oldies:
            all_ancestors.add(old)
            
        youngsters = ont.descendants(matched)
        youngsters = set(filter(pre_filter.match, youngsters))
        if len(oldies) < 1 and len(youngsters) < 1:
            print(onto_id+" not in neoplasm_core")
        else:
            print(str(len(oldies))+"<--"+onto_id+"-->"+str(len(youngsters)))
        if onto_id == "NCIT:C3262":
            print(oldies)
    
    ont_g = ont.get_graph()
    print(len(ont_g.nodes()))
    ont_g = ont_g.subgraph(all_ancestors)
    print(len(ont_g.nodes()))

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main(  )
