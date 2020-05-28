from os import path as path
from .output_preparation import get_id_label_for_prefix

################################################################################

def biosample_table_header(**config):
    """podmd

 
    podmd"""

    io_params = config[ "io_params" ]
    io_prefixes = config[ "io_prefixes" ]

    header_labs = [ ]

    for par in io_params.keys():
        header_labs.append( par )
    for pre in io_prefixes:
        header_labs.append( pre+"::id" )
        header_labs.append( pre+"::label" )

    return( header_labs )

################################################################################

def write_biosamples_template_file(**config):

    btf = path.join( config[ "paths" ][ "module_root" ], *config[ "paths" ][ "biosamples_template_file" ] )

    with open( btf, 'w' ) as bt:
        header = biosample_table_header( **config )   
        bt.write( "\t".join( header ) + "\n" )

################################################################################

def get_nested_value(parent, dotted_key):

    ps = dotted_key.split('.')

    v = ""

    if len(ps) == 1:
        try:
            v = parent[ ps[0] ]
        except:
            v = ""
    elif len(ps) == 2:
        try:
            v = parent[ ps[0] ][ ps[1] ]
        except:
            v = ""
    elif len(ps) == 3:
        try:
            v = parent[ ps[0] ][ ps[1] ][ ps[2] ]
        except:
            v = ""
    elif len(ps) == 4:
        try:
            v = parent[ ps[0] ][ ps[1] ][ ps[2] ][ ps[3] ]
        except:
            v = ""
    elif len(ps) == 5:
        try:
            v = parent[ ps[0] ][ ps[1] ][ ps[2] ][ ps[3] ][ ps[4] ]
        except:
            v = ""
    elif len(ps) > 5:
        print("¡¡¡ Parameter key "+dotted_key+" nested too deeply (>5) !!!")

    return( v )

################################################################################

def assign_nested_value(parent, dotted_key, v):

    ps = dotted_key.split('.')

    updated = parent

    if len(ps) > 5:
        print("¡¡¡ Parameter key "+dotted_key+" nested too deeply (>5) !!!")
    elif len(ps) == 5:
        try:
            updated[ ps[0] ][ ps[1] ][ ps[2] ][ ps[3] ][ ps[4] ] = v
        except:
            pass
    elif len(ps) == 4:
        try:
            updated[ ps[0] ][ ps[1] ][ ps[2] ][ ps[3] ] = v
        except:
            pass
    elif len(ps) == 3:
        try:
            updated[ ps[0] ][ ps[1] ][ ps[2] ] = v
        except:
            pass
    elif len(ps) == 2:
        try:
            updated[ ps[0] ][ ps[1] ] = v
        except:
            pass
    elif len(ps) == 1:
        try:
            updated[ ps[0] ] = v
        except:
            pass

    return( updated )


################################################################################

def assign_value_type(v, v_type):

    if v_type:
        if v_type == "float":
            if v:
                v = float(v)
        elif v_type == "integer":
            if v:
                v = int(v)
    if v == None:
        v = ""

    return( v )


