from os import path as path
from os import rename as rename
from pymongo import MongoClient
from .output_preparation import get_id_label_for_prefix
from .output_preparation import callsets_add_metadata
from .tabulating_tools import *

################################################################################

def write_biosamples_table(**kwargs):
    """podmd

    Export parameters are provided in the form

    parameter: `collection.attribute(.child_attribute)(.grandchild_attribute)(::prefix)`
    label: xxxxx

    * if a prefix is provided, the export parameters for this parameter become
        - (^...).id    
        - (^...).label    
        ... where the `id` value matches the prefix

    podmd"""

    io_params = kwargs[ "config" ][ "io_params" ]
    io_prefixes = kwargs[ "config" ][ "io_prefixes" ]
    biosfl = kwargs["config"][ "paths" ][ "biosamples_file_label" ]
    filter_defs = kwargs[ "filter_defs" ]
    args = kwargs[ "args" ]
    label = ""
    if args.label:
        label = args.label

    tab = kwargs[ "config" ][ "const" ][ "tab_sep" ]
    dash = kwargs[ "config" ][ "const" ][ "dash_sep" ]
    tmp_bios_file = "_tmp-"+biosfl

    dataset_id = kwargs[ "dataset_id" ]
    query = { "_id": { "$in": kwargs[ "biosamples::_id" ] } }

    bios_coll = MongoClient( )[ dataset_id ][ "biosamples" ]

    bios_no = 0

    biosf = open( tmp_bios_file, 'w' )

    header = biosample_table_header( **kwargs[ "config" ] )
    
    biosf.write( tab.join( header ) + "\n" )
    for bios in bios_coll.find(query):
        print(bios["id"])
        bios_line = [  ]
        for par in io_params.keys():
            v = get_nested_value(bios, io_params[ par ][ "db_key" ])
            v = assign_value_type(v, io_params[ par ][ "type" ])
            bios_line.append( str(v) )
        for pre in io_prefixes:
            pre_id, pre_lab = get_id_label_for_prefix(bios["biocharacteristics"]+bios["external_references"], pre, **kwargs)
            bios_line.append( pre_id )
            if not pre_lab:
                pre_lab = str("")
            bios_line.append( pre_lab )

        biosf.write( tab.join( bios_line ) + "\n" )
        bios_no += 1

    biosf.close()
    biosamples_file = path.join( kwargs[ "config" ][ "paths" ][ "out" ], dash.join([ dataset_id, label, str(bios_no), biosfl ]) )
    rename(tmp_bios_file, biosamples_file)

    print(str(bios_no)+" biosamples were written to "+biosamples_file)

################################################################################

def write_callsets_matrix_files(**kwargs):

    io_prefixes = kwargs[ "config" ][ "io_prefixes" ]
    smfl = kwargs["config"][ "paths" ][ "status_matrix_file_label" ]
    vmfl = kwargs["config"][ "paths" ][ "values_matrix_file_label" ]
    
    dataset_id = kwargs[ "dataset_id" ]

    mongo_client = MongoClient( )
    mongo_db = mongo_client[ dataset_id ]
    mongo_coll = mongo_db[ 'callsets' ]

    tab = kwargs[ "config" ][ "const" ][ "tab_sep" ]
    dash = kwargs[ "config" ][ "const" ][ "dash_sep" ]
    tmp_status_matrix_file = "_tmp-"+smfl
    tmp_values_matrix_file = "_tmp-"+vmfl
    args = kwargs[ "args" ]
    label = ""
    if args.label:
        label = args.label
        
    smf = open( tmp_status_matrix_file, 'w' )
    vmf = open( tmp_values_matrix_file, 'w' )
    sm_no = 0
    vm_no = 0
    for cs in mongo_coll.find({"_id": {"$in": kwargs["callsets::_id"] }}) :
        cs = callsets_add_metadata( cs, **kwargs )
        cs_meta = [ cs[ "id" ] ]
        for pre in io_prefixes:
            pre_id, pre_label = "", ""
            if cs[ pre+"::id" ]:
                pre_id = cs[ pre+"::id" ]
            if cs[ pre+"::label" ]:
                pre_label = cs[ pre+"::label" ]
            cs_meta.append(pre_id)
            cs_meta.append(pre_label)

        if "dupmap" in cs["info"][ "statusmaps" ]:
            if cs[ "info" ][ "statusmaps" ][ "dupmap" ] is not None:
                smf.write( tab.join( [ tab.join( cs_meta ), tab.join( cs[ "info" ][ "statusmaps" ][ "dupmap" ] ),
                    tab.join( cs[ "info" ][ "statusmaps" ][ "delmap" ] ) ] ) + "\n" )
                sm_no += 1
        if "dupmax" in cs["info"][ "statusmaps" ]:
            if cs[ "info" ][ "statusmaps" ][ "dupmax" ] is not None:
                vmf.write( tab.join( [ tab.join( cs_meta ), tab.join( str(x) for x in cs[ "info" ][ "statusmaps" ][ "dupmax" ] ),
                tab.join( str(x) for x in cs[ "info" ][ "statusmaps" ][ "delmin" ] ) ] ) + "\n" )
                vm_no += 1
    smf.close()
    vmf.close()
    mongo_client.close()

    status_matrix_file = path.join( kwargs[ "config" ][ "paths" ][ "out" ], dash.join([ dataset_id, label, str(sm_no), smfl ]) )
    values_matrix_file = path.join( kwargs[ "config" ][ "paths" ][ "out" ], dash.join([ dataset_id, label, str(vm_no), vmfl ]) )

    rename(tmp_status_matrix_file, status_matrix_file)
    rename(tmp_values_matrix_file, values_matrix_file)

    print(str(sm_no)+" callsets were written to "+status_matrix_file)
    print(str(vm_no)+" callsets were written to "+values_matrix_file)

################################################################################

def write_tsv_from_list(**kwargs):

    tab = kwargs[ "config" ][ "const" ][ "tab_sep" ]
    tsv = open( kwargs[ "output_file" ], 'w' )
    for line in kwargs[ "output_data" ]:
        tsv.write( tab.join( line ) + "\n" )
    tsv.close
    
