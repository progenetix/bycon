from os import path as path

################################################################################

def biosample_table_header(**datatables):
    """podmd

 
    podmd"""

    io_params = datatables[ "io_params" ]
    io_prefixes = datatables[ "io_prefixes" ]

    header_labs = [ ]

    for par in io_params.keys():
        header_labs.append( par )
    for pre in io_prefixes:
        header_labs.append( pre+"::id" )
        header_labs.append( pre+"::label" )

    return header_labs

################################################################################

def write_biosamples_template_file(**config):

    btf = path.join( config[ "paths" ][ "module_root" ], *config[ "paths" ][ "biosamples_template_file" ] )

    with open( btf, 'w' ) as bt:
        header = biosample_table_header( **config )   
        bt.write( "\t".join( header ) + "\n" )

################################################################################

def get_id_label_for_prefix(data_list, prefix, **byc):

    # not exactly doing a "prefix" match, since `geo:GSM` vs `geo:GSE` covered

    pre_id = ""
    pre_lab = ""
    for item in data_list:
        if re.compile( r"^"+prefix ).match(item["type"]["id"]):
            pre_id = item["type"]["id"]
            if "label" in item["type"]:
                pre_lab = item["type"]["label"]

    return(pre_id, pre_lab)

################################################################################

def get_nested_value(parent, dotted_key):

    ps = dotted_key.split('.')

    if len(ps) == 1:
        try:
            return parent[ ps[0] ]
        except:
            return False
    else:
        current_key = ps[0]
        if current_key in parent.keys():
            get_nested_value(parent[current_key], '.'.join(ps[1:]))
        else:
            return False
            
################################################################################

def assign_nested_value(parent, dotted_key, v):

    ps = dotted_key.split('.')

    if len(ps) == 1:
        parent[dotted_key] = v
        return parent
    else:
        current_key = ps[0]
        if current_key in parent.keys():
            parent[current_key].update(assign_nested_dict(parent[current_key], '.'.join(ps[1:]), v))
            return parent
        else:
            parent[current_key] = assign_nested_dict({}, '.'.join(ps[1:]), v)
            return parent

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

    return v


