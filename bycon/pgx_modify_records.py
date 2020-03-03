from pymongo import MongoClient
from pyexcel import get_sheet
from os import path as path
import re

################################################################################

def pgx_read_mappings(**kwargs):

    equivmaps = [ ]

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
        if re.compile( "^\w+?::\w+?$" ).match(col_name):
            print(col_name+": "+str(hi))
            col_inds[ col_name ] = hi
            
        hi += 1
        
    for i in range(1, len(table)):
        equiv_line = { }
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
            print(str(fi)+": "+equiv_line[ "ncit::id" ])
    
    print("mappings: "+str(fi))
    return equivmaps

################################################################################

def pgx_update_biocharacteristics(**kwargs):

    equiv_keys = ["icdom::id", "icdom::label", "icdot::id", "icdot::label", "ncit::id", "ncit::label"]
    update_report = [ [ "id" ] ]
    update_report[0].extend( equiv_keys )
    update_report[0].extend( [ "replaced_ncit::id", "replaced_ncit::label" ] )
    update_collection = kwargs["update_collection"]
    
    mongo_client = MongoClient( )
    mongo_db = mongo_client[ kwargs[ "dataset_id" ] ]
    mongo_coll = mongo_db[ update_collection ]
    
    db_key = kwargs["filter_defs"]["icdom"][ "scopes" ][ update_collection ][ "db_key" ]
    
    sample_no = 0
    for equivmap in kwargs["equivmaps"]:
        if not equivmap.get("icdom::id"):
            continue
        if not equivmap.get("icdot::id"):
            continue
        if not equivmap.get("ncit::id"):
            continue
        if not re.compile( kwargs["filter_defs"]["icdom"]["pattern"] ).match(equivmap["icdom::id"]):
            continue
        if not re.compile( kwargs["filter_defs"]["icdot"]["pattern"] ).match(equivmap["icdot::id"]):
            continue
        if not re.compile( kwargs["filter_defs"]["ncit"]["pattern"] ).match(equivmap["ncit::id"]):
            continue
        
        query = { "$and": [ {db_key: equivmap["icdom::id"]}, {db_key: equivmap["icdot::id"]} ] }
        for item in mongo_coll.find( query ):
            update_flag = 0
            new_biocs = [ ]
            for bioc in item[ "biocharacteristics" ]:               
                if re.compile( "ncit" ).match(bioc["type"]["id"]):
                    if bioc["type"]["id"] != equivmap["ncit::id"]:

                        report = [ item[ "id" ] ]
                        report.extend( str(equivmap[x]) for x in equiv_keys )
                        report.extend( [ str(bioc["type"]["id"]), str(bioc["type"]["label"]) ] )
                        update_report.append(report)
            
                        bioc["type"]["id"] = equivmap["ncit::id"]
                        bioc["type"]["label"] = equivmap["ncit::label"]
                        update_flag = 1
                new_biocs.append( bioc )
            if update_flag == 1:
                item[ "biocharacteristics" ] = new_biocs
                mongo_coll.update_one( { "_id" : item[ "_id" ] }, { "$set": { "biocharacteristics": new_biocs } } )
                sample_no +=1            

    mongo_client.close()
    print(kwargs[ "dataset_id" ]+": "+str(sample_no))
    return(update_report)

################################################################################

