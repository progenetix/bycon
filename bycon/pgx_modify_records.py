from pymongo import MongoClient
from pyexcel import get_sheet
from os import path as path
from datetime import datetime, date
import re, yaml

################################################################################

def pgx_read_mappings(**kwargs):

    equivmaps = [ ]
    equiv_keys = ["icdom::id", "icdom::label", "icdot::id", "icdot::label", "ncit::id", "ncit::label"]
#     equiv_keys.extend( [ ( "query::"+ek ) for ek in equiv_keys ] )
       
    try:
        table = get_sheet(file_name=kwargs[ "config" ][ "paths" ][ "mapping_file" ])
    except:
        print("No matching mapping file could be found!")
        exit()
        
    header = table[0]
    col_inds = { }
    hi = 0
    fi = 0
    for col_name in header:
        if col_name in equiv_keys:
            print(col_name+": "+str(hi))
            col_inds[ col_name ] = hi
            
        hi += 1
        
    for i in range(1, len(table)):
        equiv_line = { }
        col_match_count = 0
        for col_name in col_inds:
            try:
                cell_val = table[ i, col_inds[ col_name ] ]
                cell_val.replace("NCIT:", "ncit:")
                equiv_line[ col_name ] = cell_val
            except:
                continue
        if equiv_line.get("ncit::id"):
            equivmaps.append(equiv_line)
            fi += 1
#             print(str(fi)+": "+equiv_line[ "ncit::id" ])
    
    print("mappings: "+str(fi))
    return(equiv_keys, equivmaps)

################################################################################

def pgx_write_mappings_to_yaml(**kwargs):

    
    example_max = 4
        
    if not kwargs[ "config" ][ "paths" ].get("icdomappath"):
        print("No existing icd YAML output path was provided with -y ...")
        return()
        
 
    if not path.isdir(kwargs[ "config" ][ "paths" ][ "icdomappath" ]):
        print("No existing icd YAML output path was provided with -y ...")
        return()
        
    equivmaps = kwargs["equivmaps"]

    for dataset_id in kwargs["config"]["dataset_ids"]:

        mongo_client = MongoClient( )
        mongo_db = mongo_client[ dataset_id ]
        mongo_coll = mongo_db[ "biosamples" ]

        for equivmap in equivmaps:

            if not _check_equivmap_data(equivmap, kwargs["equiv_keys"], kwargs["filter_defs"]):
                print("\nWrong format for mapping code(s):")
                print(equivmap)
                continue

            if not equivmap.get( "examples" ):
                equivmap["examples"] = [ ]
            if len(equivmap["examples"]) < example_max:

                query = { "$and": [ {"biocharacteristics.type.id": equivmap["icdom::id"]}, {"biocharacteristics.type.id": equivmap["icdot::id"]} ] }
 
                for item in mongo_coll.find( query ):

                    if item[ "description" ] not in equivmap["examples"]:
                        if len(equivmap["examples"]) < example_max:
                            equivmap["examples"].append( item[ "description" ] )
                        else:
                            continue            
        mongo_client.close()
        
    for equivmap in equivmaps:
    
        if not _check_equivmap_data(equivmap, kwargs["equiv_keys"], kwargs["filter_defs"]):
            continue
            
        if equivmap["icdom::id"] == 'icdom-99999':
            continue
        elif equivmap["icdot::id"] == 'icdot-C99.9':
            continue

        re_map = {
            'input':[
                { 'id': equivmap["icdom::id"], 'label' : equivmap["icdom::label"] },
                { 'id': equivmap["icdot::id"], 'label' : equivmap["icdot::label"] }
            ],
            'equivalents':[
                { 'id' : equivmap["ncit::id"], 'label' : equivmap["ncit::label"] }
            ],
            'examples': equivmap.get("examples"),
            'updated': date.today().isoformat()
        }
                
        yaml_name = equivmap["icdom::id"]+','+equivmap["icdot::id"]+'.yaml'
        
        with open(path.join( kwargs[ "config" ][ "paths" ][ "icdomappath" ], yaml_name ), 'w') as yf:
            yaml.safe_dump(re_map, yf, default_flow_style=False)
    

################################################################################

def pgx_update_biocharacteristics(**kwargs):

    update_report = [ [ "id" ] ]
    update_report[0].extend( kwargs["equiv_keys"] )
    update_report[0].extend( [ "replaced_ncit::id", "replaced_ncit::label" ] )
    update_collection = kwargs["update_collection"]
        
    mongo_client = MongoClient( )
    mongo_db = mongo_client[ kwargs[ "dataset_id" ] ]
    mongo_coll = mongo_db[ update_collection ]
    
    db_key = kwargs["filter_defs"]["icdom"][ "scopes" ][ update_collection ][ "db_key" ]
    
    sample_no = 0
    for equivmap in kwargs["equivmaps"]:

        if not _check_equivmap_data(equivmap, kwargs["equiv_keys"], kwargs["filter_defs"]):
            print("\nWrong format for mapping code(s):")
            print(equivmap)
            continue
        
        query = { "$and": [ {db_key: equivmap["icdom::id"]}, {db_key: equivmap["icdot::id"]} ] }
        if equivmap["icdom::id"] == 'icdom-99999':
            query = { db_key: equivmap["icdot::id"] }
        elif equivmap["icdom::id"] == 'icdot-C99.9':
            query = { db_key: equivmap["icdom::id"] }
        
        for item in mongo_coll.find( query ):
            update_flag = 0
            new_biocs = [ ]
            for bioc in item[ "biocharacteristics" ]:               
                if re.compile( "ncit" ).match(bioc["type"]["id"]):
                    if bioc["type"]["id"] != equivmap["ncit::id"] or bioc["type"]["label"] != equivmap["ncit::label"]:

                        report = [ item[ "id" ] ]
                        report.extend( str(equivmap[x]) for x in kwargs["equiv_keys"] )
                        report.extend( [ str(bioc["type"]["id"]), str(bioc["type"]["label"]) ] )
                        update_report.append(report)
            
                        bioc["type"]["id"] = equivmap["ncit::id"]
                        bioc["type"]["label"] = equivmap["ncit::label"]
                        update_flag = 1

                new_biocs.append( bioc )

            if update_flag == 1:
                mongo_coll.update_one( { "_id" : item[ "_id" ] }, { "$set": { "biocharacteristics": new_biocs, "updated": datetime.now() } } )
                sample_no +=1

    mongo_client.close()
    print(kwargs[ "dataset_id" ]+": "+str(sample_no))
    return(update_report)

################################################################################

def _check_equivmap_data(equivmap, equiv_keys, filter_defs):

    status = True

    for f_key in equiv_keys:
        if not equivmap.get( f_key ):
            status = False
        else:
            pre, kind = f_key.split("::")
            if kind == "id":
                if not re.compile( filter_defs[ pre ]["pattern"] ).match(equivmap[ f_key ]):
                    status = False

    return status
    
