from pymongo import MongoClient
from pyexcel import get_sheet
from os import path as path
from datetime import datetime, date
from progress.bar import IncrementalBar
import re, yaml, json
from isodate import parse_duration
from .tabulating_tools import *

################################################################################
################################################################################
################################################################################

def pgx_update_samples_from_file( ds_id, **kwargs ):
    
    filter_defs = kwargs[ "filter_defs" ]
    mongo_client = MongoClient( )
    mongo_db = mongo_client[ ds_id ]
    bios_coll = mongo_db[ "biosamples" ]
    io_params = kwargs[ "config" ][ "io_params" ]
    io_prefixes = kwargs[ "config" ][ "io_prefixes" ]

    # relevant sheet is the first one...
    try:
        table = get_sheet(file_name=kwargs[ "config" ][ "paths" ][ "update_file" ])
    except Exception as e:
        print(e)
        print("No matching update file could be found!")
        exit()

    header = table[0]
    col_inds = { }
    hi = 0
    for col_name in header:
        if col_name in io_params.keys() or col_name in io_prefixes:
            print(col_name+": "+str(hi))
            col_inds[ col_name ] = hi
        hi += 1
        
    for i in range(1, len(table)):
        if not table[ i, col_inds[ "id" ] ]:
            break
        print(str(i)+": "+table[ i, col_inds[ "id" ] ])
        query = { "id": table[ i, col_inds[ "id" ] ] }
        bios = bios_coll.find_one( query )
        update = bios.copy()
        update.update( { "updated": datetime.now() } )
        for s_par in io_params.keys():
            if s_par == "id":
                continue
            try:
                if re.compile( r'\w' ).match( table[ i, col_inds[ s_par ] ] ):
                    update = assign_nested_value(update, io_params[ s_par ][ "db_key" ], table[ i, col_inds[ s_par ] ])
                    # print(update)
                    # update[ simple_par ] = table[ i, col_inds[ simple_par ] ]
            except Exception as e:
                pass
        for par_scope in [ "biocharacteristics", "external_references" ]:
            update[ par_scope ] = [ ]
            for pre in io_prefixes:
                if not par_scope in filter_defs[ pre ][ "db_key" ]:
                    continue
                u_par = { "type": {} }
                exists = False

                # first evaluation if existing parameter has to be modified
                for par in bios[ par_scope ]:
                    try:
                        if re.compile( filter_defs[ pre ][ "pattern" ] ).match( par[ "type" ][ "id" ] ):
                            try:
                                row, col = i, int( col_inds[ pre+"::id" ] )
                                if re.compile( filter_defs[ pre ][ "pattern" ] ).match( table[ row, col ] ):
                                    u_par[ "type" ][ "id" ] = table[ row, col ]
                                    u_par[ "type" ][ "label" ] = table[ i, col_inds[ pre+"::label" ] ]
                                    print(u_par[ "type" ][ "id" ])
                                    exists = True
                                else:
                                    u_par = par
                                    exists = True
                            except Exception:
                                pass
                    except Exception as e:
                        pass                

                # if not there => new
                if exists == False:
                    try:
                        if re.compile( filter_defs[ pre ][ "pattern" ] ).match( table[ i, col_inds[ pre+"::id" ] ] ):
                                u_par[ "type" ][ "id" ] = table[ i, col_inds[ pre+"::id" ] ]
                                u_par[ "type" ][ "label" ] = table[ i, col_inds[ pre+"::label" ] ]
                                exists = True
                    except Exception as e:
                        pass

                if exists == True:
                    update[ par_scope ].append( u_par )

            # 
            if kwargs[ "args"].test:
                print( json.dumps(update, indent=4, sort_keys=True, default=str) )
            else:
                bios_coll.update_one( { "_id" : bios[ "_id" ] }, { "$set": update } )


################################################################################
################################################################################
################################################################################

def pgx_read_icdom_ncit_defaults(**kwargs):

    defmaps = [ ]
    equiv_keys = ["icdom::id", "icdom::label", "icdom::level", "NCIT::id", "NCIT::label"]

    print(kwargs[ "config" ][ "paths" ][ "mapping_file" ])       
    try:
        table = get_sheet(file_name=kwargs[ "config" ][ "paths" ][ "mapping_file" ], sheet_name="ICDOM-NCIT-defaults")
    except Exception as e:
        print(e)
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
                equiv_line[ col_name ] = cell_val
            except:
                continue
        if equiv_line.get("NCIT::id"):
            defmaps.append(equiv_line)
            fi += 1
    
    print("default mappings: "+str(fi))
    return(defmaps)

################################################################################
################################################################################
################################################################################

def pgx_read_mappings(**kwargs):

    equivmaps = [ ]
    equiv_keys = ["icdom::id", "icdom::label", "icdot::id", "icdot::label", "NCIT::id", "NCIT::label"]

    print(kwargs[ "config" ][ "paths" ][ "mapping_file" ])       
    try:
        table = get_sheet(file_name=kwargs[ "config" ][ "paths" ][ "mapping_file" ], sheet_name="ICDOM-ICDOT-NCIT-matched")
    except Exception as e:
        print(e)
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
                equiv_line[ col_name ] = cell_val
            except:
                continue
        if equiv_line.get("NCIT::id"):
            equivmaps.append(equiv_line)
            fi += 1
    
    print("mappings: "+str(fi))
    return(equiv_keys, equivmaps)

################################################################################
################################################################################
################################################################################

def get_current_mappings(**kwargs):

    equiv_keys = ["icdom::id", "icdom::label", "icdot::id", "icdot::label", "NCIT::id", "NCIT::label"]

    equiv_dic = { }
    for e in kwargs["equivmaps"]:
        if not _check_equivmap_data(e, kwargs["equiv_keys"], kwargs["filter_defs"]):
            continue
        e_k = e[ "icdom::id" ]+"::"+e[ "icdot::id" ]
        equiv_dic.update( { e_k: e } )
    
    map_dic = { }

    for ds_id in kwargs["config"]["dataset_ids"]:

        mongo_client = MongoClient( )
        mongo_db = mongo_client[ ds_id ]
        bios_coll = mongo_db[ "biosamples" ]
        
        bar = IncrementalBar(ds_id+' samples', max = bios_coll.estimated_document_count() )

        split_v = re.compile(r'^(\w+?)[\:\-](\w[\w\.]+?)$')

        for bios in bios_coll.find( { } ):

            b = { k: "" for k in equiv_keys }
            b[ "status" ] = "TODO"
 
            for bioc in bios[ "biocharacteristics" ]:
                if split_v.match( bioc[ "type" ][ "id" ] ):
                    pre, code = split_v.match(bioc[ "type" ][ "id" ]).group(1, 2)
                    b[ pre+"::id" ] = bioc[ "type" ][ "id" ]
                    b[ pre+"::label" ] = bioc[ "type" ][ "label" ]
                else:
                    continue

            b_k = b[ "icdom::id" ]+"::"+b[ "icdot::id" ]
            if b_k in equiv_dic.keys():
                b[ "status" ] = "ok"

            map_dic.update( { b_k: b } )

            bar.next()

        bar.finish()

        todo = 0

    t_k = equiv_keys
    t_k.append( "status" )
    od = [ t_k ]

    for m in sorted(map_dic.keys()):
        if map_dic[ m ]["status"] == "TODO":
            todo += 1
        l = [ str(map_dic[ m ][ k ]) for k in t_k ]
        od.append( l )

    print("=> {} ICD-O combinations ({} to be reviewed)".format(len(map_dic), todo) )

    return(od)

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

    for ds_id in kwargs["config"]["dataset_ids"]:

        bar = IncrementalBar(ds_id+ ' example lookup', max = len(equivmaps))

        mongo_client = MongoClient( )
        mongo_db = mongo_client[ ds_id ]
        mongo_coll = mongo_db[ "biosamples" ]

        for e in equivmaps:

            bar.next()

            if not _check_equivmap_data(e, kwargs["equiv_keys"], kwargs["filter_defs"]):
                print("\nWrong format for mapping code(s):")
                print(e)
                continue

            if not e.get( "examples" ):
                e[ "examples" ] = [ ]
            if len(e["examples"]) < example_max:

                query = { "$and": [ {"biocharacteristics.type.id": e[ "icdom::id" ]}, {"biocharacteristics.type.id": e[ "icdot::id" ]} ] }
 
                for item in mongo_coll.find( query ):

                    if item[ "description" ] not in e["examples"]:
                        if len(e[ "examples" ]) < example_max:
                            e[ "examples" ].append( item[ "description" ] )
                        else:
                            continue            
        mongo_client.close()
        bar.finish()
        
    for e in equivmaps:
    
        if not _check_equivmap_data(e, kwargs["equiv_keys"], kwargs["filter_defs"]):
            continue

        icdmap = _format_icdmap( e )
            
        yaml_name = e[ "icdom::id" ]+','+e[ "icdot::id" ]+'.yaml'
        
        with open(path.join( kwargs[ "config" ][ "paths" ][ "icdomappath" ], yaml_name ), 'w') as yf:
            yaml.safe_dump(icdmap, yf, default_flow_style=False)

################################################################################
################################################################################
################################################################################

def pgx_rewrite_icdmaps_db( **kwargs ):

    mongo_client = MongoClient( )
    mappings_coll = mongo_client[ "progenetix" ][ "icdmaps" ]
    mappings_coll.delete_many( {} )
 
    for e in kwargs["equivmaps"]:

        if not _check_equivmap_data(e, kwargs["equiv_keys"], kwargs["filter_defs"]):
            continue

        icdmap = _format_icdmap( e )

        mappings_coll.insert_one( icdmap )

################################################################################
################################################################################
################################################################################

def _format_icdmap( e ):

    icdmap = {
        'input':[
            { 'id': e["icdom::id"], 'label' : e["icdom::label"] },
            { 'id': e["icdot::id"], 'label' : e["icdot::label"] }
        ],
        'equivalents':[
            { 'id' : e["NCIT::id"], 'label' : e["NCIT::label"] }
        ],
        'examples': e.get("examples"),
        'updated': date.today().isoformat()
    }

    return(icdmap)
   
################################################################################
################################################################################
################################################################################

def pgx_update_biocharacteristics( ds_id, **kwargs):

    update_report = [ "id",  *kwargs["equiv_keys"], "replaced_ncit::id", "replaced_ncit::label" ]
        
    mongo_client = MongoClient( )
    mongo_db = mongo_client[ ds_id ]
    mongo_coll = mongo_db[ kwargs["update_collection"] ]
    
    db_key = kwargs["filter_defs"]["icdom"][ "db_key" ]


    # default NCIT per icdom, in several levels...
    sample_no = 0
    for n in (1,2,3,4):
        for e in kwargs["defmaps"]:
            if e[ "icdom::level" ] == n:                
                query = { db_key: {"$regex": e["icdom::id"] } }
                m_no = mongo_coll.find( query ).count()
                if m_no > 0:
                    print("=> level {}, {}, {}".format(n, e["icdom::id"], m_no) )
                    for s in mongo_coll.find( query ):
                        sample_no, update_report = update_sample_ncit(sample_no, s, e, mongo_coll, update_report, False, **kwargs)

    # manually mapped icdom + icdot => NCIT mappings
    bar = IncrementalBar('mappings', max = len(kwargs["equivmaps"]))    
    sample_no = 0
    for e in kwargs["equivmaps"]:
        bar.next()

        if not _check_equivmap_data(e, kwargs["equiv_keys"], kwargs["filter_defs"]):
            print("\nWrong format for mapping code(s): {}".format(e))
            continue
        
        query = { "$and": [ {db_key: e["icdom::id"]}, {db_key: e["icdot::id"]} ] }

        for s in mongo_coll.find( query ):
            sample_no, update_report = update_sample_ncit(sample_no, s, e, mongo_coll, update_report, True, **kwargs)
    bar.finish()   

    mongo_client.close()
    print(ds_id+": "+str(sample_no))
    return(update_report)

################################################################################
################################################################################
################################################################################

def update_sample_ncit(sample_no, s, e, mongo_coll, update_report, report_flag, **kwargs):

    update_flag = 0
    new_biocs = [ ]
    for bioc in s[ "biocharacteristics" ]:               
        if re.compile( "NCIT" ).match(bioc["type"]["id"]):
            if bioc["type"]["id"] != e["NCIT::id"] or bioc["type"]["label"] != e["NCIT::label"]:

                if report_flag:

                    report = [ s[ "id" ] ]
                    report.extend( format( e[x] ) for x in kwargs["equiv_keys"] )
                    report.extend( [ str(bioc["type"]["id"]), str(bioc["type"]["label"]) ] )
                    update_report.append(report)
    
                bioc["type"]["id"] = e["NCIT::id"]
                bioc["type"]["label"] = e["NCIT::label"]
                update_flag = 1

        # all biocs are collected, since whole list will be replaced
        new_biocs.append( bioc )

    ncit_exists = 0
    for nbc in new_biocs:
        if re.compile( "NCIT" ).match(nbc["type"]["id"]):
            ncit_exists = 1

    if not ncit_exists == 1:
        new_biocs.append( { "type": { "id": e["NCIT::id"], "label": e["NCIT::label"] } } )
        update_flag = 1

    if update_flag == 1:
        mongo_coll.update_one( { "_id" : s[ "_id" ] }, { "$set": { "biocharacteristics": new_biocs, "updated": datetime.now() } } )
        # print(("updated {}: {} ({})").format(s[ "_id" ], e["NCIT::id"], e["NCIT::label"]))
        sample_no +=1

    return(sample_no, update_report)

################################################################################
################################################################################
################################################################################

def _check_equivmap_data(e, equiv_keys, filter_defs):

    status = True

    for f_key in equiv_keys:
        if not e.get( f_key ):
            status = False
        else:
            pre, kind = f_key.split("::")
            if kind == "id":
                if not re.compile( filter_defs[ pre ]["pattern"] ).match(e[ f_key ]):
                    status = False

    if e[ "icdom::id" ] == 'icdom-99999':
        status = False
    elif e[ "icdot::id" ] == 'icdot-C99.9':
        status = False

    return status


