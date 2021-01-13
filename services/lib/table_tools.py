from os import path as path

################################################################################

def io_table_header(io_params, io_prefixes):
    """podmd
 
    podmd"""

    header_labs = [ ]

    for collection, pars in io_params.items():
        if collection is 'non_collection':
            collection = ''
        else:
            collection += '.'
        for par in pars.keys():
            header_labs.append( collection+par )
    for collection, pres in io_prefixes.items():
        for pre in pres:
            header_labs.append( collection+pre+"::id" )
            header_labs.append( collection+pre+"::label" )

    return header_labs

################################################################################

def io_map_to_db(io_params, io_prefixes):

    field_to_db = { }

    for collection, fields in io_params.items():

        if collection is 'non_collection':
            continue

        for field_name, field_info in fields.items():
            field_to_db[collection+'.'+field_name] = [field_info['db_key'], field_info['type']]

    for collection, field_category in io_prefixes.items():

        for prefix in field_category:

            field_to_db[collection+'.'+prefix+'::id'] = [field_category+'.id', 'string']
            field_to_db[collection+'.'+prefix+'::label'] = [field_category+'.label', 'string']

    return field_to_db

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
        if re.compile( r"^"+prefix ).match(item["id"]):
            pre_id = item["id"]
            if "label" in item:
                pre_lab = item["label"]

    return(pre_id, pre_lab)

################################################################################

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
        try: # if field is a list -> will append
            if type(parent[dotted_key]) == list:
                parent[dotted_key] += list(v)
        except KeyError:
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

    return( v )


