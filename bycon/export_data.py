from os import path as path
from os import rename as rename
from pymongo import MongoClient

################################################################################

def write_callsets_matrix_files(**kwargs):

    bio_prefixes = kwargs[ "config" ][ "bio_prefixes" ]
    smfl = kwargs["config"][ "paths" ][ "status_matrix_file_label" ]
    vmfl = kwargs["config"][ "paths" ][ "values_matrix_file_label" ]
    
    dataset_id = kwargs[ "config" ][ "data_pars" ][ "dataset_id" ]

    mongo_client = MongoClient( )
    mongo_db = mongo_client[ dataset_id ]
    mongo_coll = mongo_db[ 'callsets' ]

    tab = kwargs[ "config" ][ "const" ][ "tab_sep" ]
    dash = kwargs[ "config" ][ "const" ][ "dash_sep" ]
    tmp_status_matrix_file = "_tmp-"+smfl
    tmp_values_matrix_file = "_tmp-"+vmfl

    smf = open( tmp_status_matrix_file, 'w' )
    vmf = open( tmp_values_matrix_file, 'w' )
    sm_no = 0
    vm_no = 0
    for cs in mongo_coll.find({"_id": {"$in": kwargs["callsets::_id"] }}) :
        cs = callsets_add_metadata( cs, **kwargs )
        cs_meta = [ cs[ "id" ] ]
        for bio_pre in bio_prefixes:
            cs_meta.append(cs[ bio_pre ])


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

    status_matrix_file = path.join( kwargs[ "config" ][ "paths" ][ "out" ], dash.join([ dataset_id, str(sm_no), smfl ]) )
    values_matrix_file = path.join( kwargs[ "config" ][ "paths" ][ "out" ], dash.join([ dataset_id, str(vm_no), vmfl ]) )

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
    
