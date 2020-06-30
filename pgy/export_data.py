from os import path as path
from os import rename as rename
from pymongo import MongoClient
from pgy.output_preparation import get_id_label_for_prefix
from pgy.output_preparation import callsets_add_metadata
from pgy.tabulating_tools import *

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

    tmp_bios_file = "_tmp-"+biosfl

    query = { "_id": { "$in": kwargs["query_results"][ "bs._id" ][ "target_values" ] } }
    ds_id = kwargs["query_results"][ "bs._id" ][ "source_db" ]

    bios_coll = MongoClient( )[ ds_id ][ "biosamples" ]

    bios_no = 0

    biosf = open( tmp_bios_file, 'w' )

    header = biosample_table_header( **kwargs[ "config" ] )
    
    biosf.write( "\t".join( header ) + "\n" )
    for bios in bios_coll.find(query):
        # print(bios["id"])
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

        biosf.write( "\t".join( bios_line ) + "\n" )
        bios_no += 1

    biosf.close()
    biosamples_file = path.join( kwargs[ "config" ][ "paths" ][ "out" ], "-".join([ ds_id, label, str(bios_no), biosfl ]) )
    rename(tmp_bios_file, biosamples_file)

    print(str(bios_no)+" biosamples were written to "+biosamples_file)

################################################################################

def write_callsets_matrix_files(**kwargs):

    io_prefixes = kwargs[ "config" ][ "io_prefixes" ]
    smfl = kwargs["config"][ "paths" ][ "status_matrix_file_label" ]
    vmfl = kwargs["config"][ "paths" ][ "values_matrix_file_label" ]
    
    query = { "_id": { "$in": kwargs["query_results"][ "cs._id" ][ "target_values" ] } }
    ds_id = kwargs["query_results"][ "bs._id" ][ "source_db" ]

    cs_coll = MongoClient( )[ ds_id ][ "callsets" ]

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
    for cs in cs_coll.find( query ) :
        cs = callsets_add_metadata( ds_id, cs, **kwargs )
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
                smf.write( "\t".join( [ "\t".join( cs_meta ), "\t".join( cs[ "info" ][ "statusmaps" ][ "dupmap" ] ),
                    "\t".join( cs[ "info" ][ "statusmaps" ][ "delmap" ] ) ] ) + "\n" )
                sm_no += 1
        if "dupmax" in cs["info"][ "statusmaps" ]:
            if cs[ "info" ][ "statusmaps" ][ "dupmax" ] is not None:
                vmf.write( "\t".join( [ "\t".join( cs_meta ), "\t".join( str(x) for x in cs[ "info" ][ "statusmaps" ][ "dupmax" ] ),
                "\t".join( str(x) for x in cs[ "info" ][ "statusmaps" ][ "delmin" ] ) ] ) + "\n" )
                vm_no += 1
    smf.close()
    vmf.close()

    status_matrix_file = path.join( kwargs[ "config" ][ "paths" ][ "out" ], "-".join([ ds_id, label, str(sm_no), smfl ]) )
    values_matrix_file = path.join( kwargs[ "config" ][ "paths" ][ "out" ], "-".join([ ds_id, label, str(vm_no), vmfl ]) )

    rename(tmp_status_matrix_file, status_matrix_file)
    rename(tmp_values_matrix_file, values_matrix_file)

    print(str(sm_no)+" callsets were written to "+status_matrix_file)
    print(str(vm_no)+" callsets were written to "+values_matrix_file)

################################################################################

def write_tsv_from_list(of, od, **config):

    tsv = open( of, 'w' )
    for l in od:
        tsv.write( "\t".join( l ) + "\n" )
    tsv.close
    
