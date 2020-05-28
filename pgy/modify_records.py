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

def pgx_update_samples_from_file( **kwargs ):
    
    filter_defs = kwargs[ "filter_defs" ]
    mongo_client = MongoClient( )
    mongo_db = mongo_client[ kwargs[ "dataset_id" ] ]
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

def pgx_populate_callset_info( **kwargs ):

    """podmd
 
    ### Denormalizing Progenetix data

    While the Progenetix data schema is highly flexible, the majority of
    database content can be expressed with a limited set of parameters.

    The `pgx_populate_callset_info` method denormalizes the main information
    from the `biosamples` collection into the corresponding `callsets`, using
    the schema-free `info` object.

    podmd"""

    mongo_client = MongoClient( )
    mongo_db = mongo_client[ kwargs[ "dataset_id" ] ]
    bios_coll = mongo_db[ "biosamples" ]
    inds_coll = mongo_db[ "individuals" ]
    cs_coll = mongo_db[ "callsets" ]

    filter_defs = kwargs[ "filter_defs" ]

    cs_query = { }
    cs_count = cs_coll.estimated_document_count()

    bar = IncrementalBar('callsets', max = cs_count)

    for cs in cs_coll.find( { } ):

        update_flag = 0
        if not "info" in cs.keys():
            cs[ "info" ] = { }

        bios = bios_coll.find_one({"id": cs["biosample_id"] })
        inds = inds_coll.find_one({"id": bios["individual_id"] })

        if not "biocharacteristics" in inds:
            inds[ "biocharacteristics" ] = [ ]

        prefixed = [ *bios[ "biocharacteristics" ], *bios[ "external_references" ], *inds[ "biocharacteristics" ]  ]

        for mapped in prefixed:
            for pre in kwargs[ "filter_defs" ]:
                try:
                    if re.compile( filter_defs[ pre ][ "pattern" ] ).match( mapped[ "type" ][ "id" ] ):
                        cs[ "info" ][ pre ] = mapped[ "type" ]
                        update_flag = 1
                        break
                except Exception:
                    pass

        if "followup_months" in bios[ "info" ]:
            try:
                if bios[ "info" ][ "followup_months" ]:
                    cs[ "info" ][ "followup_months" ] = float("%.1f" %  bios[ "info" ][ "followup_months" ])
                    update_flag = 1
            except ValueError:
                return False            

        if "death" in bios[ "info" ]:
            if bios[ "info" ][ "death" ]:
                if str(bios[ "info" ][ "death" ]) == "1":
                    cs[ "info" ][ "death" ] = "dead"
                    update_flag = 1
                elif str(bios[ "info" ][ "death" ]) == "0":
                    cs[ "info" ][ "death" ] = "alive"
                    update_flag = 1

        if "age_at_collection" in bios:
            try:
                if bios[ "age_at_collection" ][ "age" ]:    
                    if re.compile( r"P\d" ).match( bios[ "age_at_collection" ][ "age" ] ):
                        cs[ "info" ][ "age_iso" ] = bios[ "age_at_collection" ][ "age" ]
                        cs[ "info" ][ "age_years" ] = _isoage_to_decimal_years(bios[ "age_at_collection" ][ "age" ])
                        # print(cs[ "info" ][ "age_iso" ])
                        # print(cs[ "info" ][ "age_years" ])
                        update_flag = 1
            except Exception:
                pass


        if update_flag == 1:
                cs_coll.update_one( { "_id" : cs[ "_id" ] }, { "$set": { "info": cs[ "info" ], "updated": datetime.now() } } )

        bar.next()

    bar.finish()
    mongo_client.close()

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
    
    print("mappings: "+str(fi))
    return(equiv_keys, defmaps)

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

    for dataset_id in kwargs["config"]["dataset_ids"]:

        mongo_client = MongoClient( )
        mongo_db = mongo_client[ dataset_id ]
        bios_coll = mongo_db[ "biosamples" ]
        
        bar = IncrementalBar(dataset_id+' samples', max = bios_coll.estimated_document_count() )

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
        # print("{}: {} - {}".format(dataset_id, m, map_dic[ m ]["status"]))
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

    for dataset_id in kwargs["config"]["dataset_ids"]:

        bar = IncrementalBar(dataset_id+ ' example lookup', max = len(equivmaps))

        mongo_client = MongoClient( )
        mongo_db = mongo_client[ dataset_id ]
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

def pgx_update_biocharacteristics(**kwargs):

    update_report = [ [ "id" ] ]
    update_report[0].extend( kwargs["equiv_keys"] )
    update_report[0].extend( [ "replaced_ncit::id", "replaced_ncit::label" ] )
        
    mongo_client = MongoClient( )
    mongo_db = mongo_client[ kwargs[ "dataset_id" ] ]
    mongo_coll = mongo_db[ kwargs["update_collection"] ]
    
    db_key = kwargs["filter_defs"]["icdom"][ "db_key" ]

    bar = IncrementalBar('mappings', max = len(kwargs["equivmaps"]))
    
    sample_no = 0

    for equivmap in kwargs["equivmaps"]:

        bar.next()

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
                if re.compile( "NCIT" ).match(bioc["type"]["id"]):
                    if bioc["type"]["id"] != equivmap["NCIT::id"] or bioc["type"]["label"] != equivmap["NCIT::label"]:

                        report = [ item[ "id" ] ]
                        report.extend( str(equivmap[x]) for x in kwargs["equiv_keys"] )
                        report.extend( [ str(bioc["type"]["id"]), str(bioc["type"]["label"]) ] )
                        update_report.append(report)
            
                        bioc["type"]["id"] = equivmap["NCIT::id"]
                        bioc["type"]["label"] = equivmap["NCIT::label"]
                        update_flag = 1

                # all biocs are collected, since whole list will be replaced
                new_biocs.append( bioc )

            ncit_exists = 0
            for nbc in new_biocs:
                if re.compile( "NCIT" ).match(nbc["type"]["id"]):
                    ncit_exists = 1

            if not ncit_exists == 1:
                new_biocs.append( { "type": { "id": equivmap["NCIT::id"], "label": equivmap["NCIT::label"] } } )
                update_flag = 1

            if update_flag == 1:
                mongo_coll.update_one( { "_id" : item[ "_id" ] }, { "$set": { "biocharacteristics": new_biocs, "updated": datetime.now() } } )
                # print(("updated {}: {} ({})").format(item[ "_id" ], equivmap["NCIT::id"], equivmap["NCIT::label"]))
                sample_no +=1

    bar.finish()   

    mongo_client.close()
    print(kwargs[ "dataset_id" ]+": "+str(sample_no))
    return(update_report)

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

################################################################################
################################################################################
################################################################################

def _isoage_to_decimal_years(isoage):

    years, months = [ 0, 0 ]
    age_match = re.compile(r"^P(?:(\d+?)Y)?(?:(\d+?))?")
    if age_match.match(isoage):
        y, m = age_match.match(isoage).group(1,2)
        if y:
            years = y * 1
        if m:
            months = m * 1
        dec_age = float(years) + float(months) / 12
        return float("%.1f" % dec_age)

    return

