#!/usr/local/bin/python3

import sys, yaml, re, json
from pymongo import MongoClient
from os import path as path
# from ontobio.ontol_factory import OntologyFactory
# from ontobio.assoc_factory import AssociationSetFactory
# from networkx import nx
# from networkx.readwrite import json_graph


# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *
from pgy import *

################################################################################
################################################################################
################################################################################

def main():

    """podmd

    This app creates coded hierarchies for the different disease code 
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
    config[ "paths" ][ "hier_file" ] = path.join( config[ "paths" ][ "module_root" ], "rsrc", "ncit", "Neoplasm_Core_Hierarchy_Plus.txt" )
    
    filter_defs = read_filter_definitions( **config[ "paths" ] )    

    # processing ncit
    # TODO: module, reading in the different hierarchies (ICDO-M, NCIt ...)
    prefix = "NCIT"
    pre_filter = re.compile( filter_defs[ prefix ][ "pattern" ] )

    # TODO: module, run separately for defined datasets
    mongo_client = MongoClient()
    mongo_db = mongo_client[ "progenetix" ]
    mongo_coll = mongo_db[ "biosamples" ]
    onto_ids = mongo_coll.distinct( "biocharacteristics.type.id", { "biocharacteristics.type.id": { "$regex": pre_filter } } )
    onto_ids = list(filter(pre_filter.match, onto_ids))
    # print(len(onto_ids))
        
    print("reading "+str(config[ "paths" ][ "hier_file" ]))
    hier_lines = open( config[ "paths" ][ "hier_file" ], 'r' ).readlines()  

    ONTO_IDs = list(map(str.upper, onto_ids))
    ONTO_IDs.append('NCIT:C3262')
    
    print("reading "+str(config[ "paths" ][ "mapping_file" ]))
    # ont = OntologyFactory().create( config[ "paths" ][ "mapping_file" ] )
    # ont_g = ont.get_graph()
    with open( config[ "paths" ][ "mapping_file" ], "r") as fd:
        ont = json.load( fd )

    npl_core_graph = { }

    for graph in ont["graphs"]:
        if "neoplasm-core" in graph["id"]:
            npl_core_graph = graph
    
    # print(npl_core_graph.keys())
    # print(npl_core_graph["id"])

    npl_core_ncit_graph = { "nodes": [ ], "edges": [ ] }

    hier_match = re.compile(r"^.+?NCIT[:_](C\d+?)\s*?$")

    for node in npl_core_graph["nodes"]:
        if hier_match.match(node[ "id" ]):
            node[ "id" ] = "NCIT:"+hier_match.match(node[ "id" ]).group(1)
            # print(node[ "id" ])
            npl_core_ncit_graph[ "nodes" ].append(node)

    for edge in npl_core_graph["edges"]:
        if hier_match.match(edge['sub']) and hier_match.match(edge['obj']):
            sub = "NCIT:"+hier_match.match(edge['sub']).group(1)
            obj = "NCIT:"+hier_match.match(edge['obj']).group(1)
            npl_core_ncit_graph[ "edges" ].append([sub, obj])

    for key in ["edges", "nodes"]:
        print("=> no. of {}: {}".format(key, len( npl_core_ncit_graph[ key ] ) ) )

    exit()

    
# "NCIT:C3262": "Neoplasm"
# "NCIT:C7062": "Neoplasm by Special Category"
# "NCIT:C4741": "Neoplasm by Morphology"
# "NCIT:C3263": "Neoplasm by Site"

    onto_trees = [
        { "label": "Neoplasm", "root": "NCIT:C3262", "classes": { } },
        # { "label": "Neoplasm by Morphology", "root": "NCIT:C4741", "classes": { } },
        # { "label": "Neoplasm by Site", "root": "NCIT:C3263", "classes": { } },    
    ]

    all_ancestors = set( ONTO_IDs )
    
    for idx, tree in enumerate(onto_trees):

        [root] = ont.search(tree["root"])
        
        print("=> processing root "+tree["root"])
   
        for onto_id in ONTO_IDs:
        
#             if onto_id == 'NCIT:C3262':
#                 continue
            
            [matched] = ont.search(onto_id)
            oldies = ont.ancestors(matched)
            oldies = set(filter(pre_filter.match, oldies))
            for old in oldies:
                all_ancestors.add(old)
            
            youngsters = ont.descendants(matched)
            youngsters = set(filter(pre_filter.match, youngsters))
            if len(oldies) < 1 and len(youngsters) < 1:
                print(onto_id+" not in neoplasm_core")
                onto_trees[ idx ][ "classes" ][ onto_id ] = { "parents": [ 'NCIT:C3262' ], "children": [ onto_id ], "core": False }
            else:
                print("{} <-- {} --> {}".format( len(oldies), onto_id, len(youngsters) ) )
                onto_trees[ idx ][ "classes" ][ onto_id ] = { "parents": oldies, "children": youngsters, "core": True }

    
        # onto_trees[ idx ][ "graph" ] = ont_g.subgraph(all_ancestors)
        # print(len(onto_trees[ idx ][ "graph" ].nodes()))
    
        # data = json_graph.node_link_data(onto_trees[ idx ][ "graph" ])
        # print("=> nodes for root "+tree["root"]+": "+str(len(data["nodes"])))
    
        # onto_dump = path.join( config[ "paths" ][ "out" ], "ontograph_"+tree[ "root" ]+".json")
        # with open(onto_dump, 'w') as fp:
        #     json.dump(data, fp)

        hier_classes = { }
        hier_match = re.compile(r"^\s*?(\w.*?) \((C\d+?)\)\s*?$")
        line_no = 0
        for line in hier_lines:
            if hier_match.match(line):
                hier_item = hier_match.match(line).group(1,2)
                hier_classes[ hier_item[1] ] = hier_item[0]
                line_no += 1
                print(("{} - {}").format(line_no, hier_classes[ hier_item[1] ]))



        print("Wrote graph JSON to "+onto_dump)
    
################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main(  )
