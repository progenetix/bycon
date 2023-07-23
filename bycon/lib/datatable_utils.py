import csv, re, requests
# from attrdictionary import AttrDict
from random import sample as randomSamples

from cgi_parsing import prjsonnice

################################################################################

def export_datatable_download(results, byc):

    # TODO: separate table generation from HTTP response

    if not "table" in byc["output"]:
        return
    if not "datatable_mappings" in byc:
        return

    dt_m = byc["datatable_mappings"]
    r_t = byc["response_entity_id"]
    io_params = dt_m["entities"][ r_t ]["parameters"]

    if not byc["response_entity_id"] in dt_m["entities"]:
        return

    if not "local" in byc["env"]:
 
        print('Content-Type: text/tsv')
        if byc["download_mode"] is True:
            print('Content-Disposition: attachment; filename='+byc["response_entity_id"]+'.tsv')
        print('status: 200')
        print()

    if "idtable" in byc["output"]:
        io_params = {"id": {"db_key":"id", "type": "string" } }

    header = create_table_header(io_params)

    print("\t".join( header ))

    for pgxdoc in results:

        line = [ ]

        for par, par_defs in io_params.items():

            parameter_type = par_defs.get("type", "string")
            pres = par_defs.get("prefix_split", {})

            if len(pres.keys()) < 1:
                db_key = par_defs.get("db_key", "___undefined___")
                v = get_nested_value(pgxdoc, db_key)
                if isinstance(v, list):
                    line.append("::".join(map(str, (v))))
                else:
                    line.append(str(v))
            else:

                par_vals = pgxdoc.get(par, [])

                # TODO: this is based on the same order of prefixes as in the
                # header generation, w/o checking; should be keyed ...
                for pre in pres.keys():
                    p_id = ""
                    p_label = ""
                    for v in par_vals:
                        if v.get("id", "___none___").startswith(pre):
                            p_id = v.get("id")
                            p_label = v.get("label", "")
                            continue
                    line.append(p_id)
                    line.append(p_label)

        print("\t".join( line ))

    exit()

################################################################################

def import_datatable_dict_line(byc, parent, fieldnames, lineobj, primary_scope="biosample"):

    dt_m = byc["datatable_mappings"]

    io_params = dt_m["entities"][ primary_scope ]["parameters"]
    def_params = create_table_header(io_params)

    pref_array_values = {}

    for f_n in fieldnames:

        if "#"in f_n:
            continue

        if f_n not in def_params:
            continue

        # this is for the split-by-prefix columns
        par = re.sub(r'___.*?$', '', f_n)
        par_defs = io_params.get(par, {})

        v = lineobj[f_n].strip()

        # if byc["debug_mode"] is True:
        #     if "analysis" in primary_scope:
        #         print(f'{f_n}: {v}')

        if len(v) < 1:
            if f_n in io_params.keys():
                v = io_params[f_n].get("default", "")

        if len(v) < 1:
            continue

        # this makes only sense for updating existing data; if there would be
        # no value, the parameter would just be excluded from the update object
        # if there was an empy value
        if "__delete__" in v.lower():
            v = ""

        parameter_type = par_defs.get("type", "string")
        if "num" in parameter_type:
            v = float(v)
        elif "integer" in parameter_type:
            v = int(v)

        if re.match(r"^(\w+[a-zA-Z0-9])_(id|label)___(\w+)$", f_n):
            p, key, pre = re.match(r"^(\w+)_(id|label)___(\w+)$", f_n).group(1,2,3)
            # TODO: this is a bit complicated - label and id per prefix ...
            if not p in pref_array_values.keys():
                pref_array_values.update({p:{pre:{}}})
            if not pre in pref_array_values[p].keys():
                pref_array_values[p].update({pre:{}})
            pref_array_values[p][pre].update({key:v})
            continue
        
        p_d = io_params.get(f_n)
        if not p_d:
            continue

        dotted_key = p_d.get("db_key")
        if not dotted_key:
            continue

        # assign_nested_attribute(parent, db_key, v)
        assign_nested_value(parent, dotted_key, v, p_d)

    for l_k, pre_item in pref_array_values.items():
        if not l_k in parent:
            parent.update({l_k:[]})
        for pre, p_v in pre_item.items():
            parent[l_k].append(p_v)

    return parent

################################################################################

def create_table_header(io_params):

    """podmd
    podmd"""

    header_labs = [ ]

    for par, par_defs in io_params.items():

        pres = par_defs.get("prefix_split", {})

        if len(pres.keys()) < 1:
            header_labs.append( par )
            continue

        for pre in pres.keys():
            header_labs.append( par+"_id"+"___"+pre )
            header_labs.append( par+"_label"+"___"+pre )

    return header_labs

################################################################################

# def assign_nested_attribute(parent, dotted_key, v):

#     n_p = AttrDict(parent)
#     keys = dotted_key.split('.')
#     for key in keys[:-1]:
#         n_p = getattr(n_p, key)
#     setattr(n_p, keys[-1], v)

#     return dict(parent)

# ################################################################################

# def get_nested_value(obj, dot_string):
#     keys = dot_string.split('.')
#     for key in keys:
#         obj = getattr(obj, key)
#     return obj

################################################################################

def assign_nested_value(parent, dotted_key, v, parameter_definitions={}):


    parameter_type = parameter_definitions.get("type", "string")
    parameter_default = parameter_definitions.get("default")

    if v is None:
        if parameter_default:
            v = parameter_default

    if v is None:
        return parent

    if "num" in parameter_type:
        if str(v).strip().lstrip('-').replace('.','',1).isdigit():
            v = float(v)
    elif "integer" in parameter_type:
        if str(v).strip().isdigit():
            v = int(v)
    else:
        v = str(v)

    ps = dotted_key.split('.')

    if len(ps) == 1:
        if "array" in parameter_type:
            parent.update({ps[0]: v.split(',')})
        else:
            parent.update({ps[0]: v })
        return parent

    if ps[0] not in parent or parent[ ps[0] ] is None:
        parent.update({ps[0]: {}})

    if len(ps) == 2:
        if "array" in parameter_type:
            parent[ ps[0] ].update({ps[1]: v.split(',')})
        else:
            parent[ ps[0] ].update({ps[1]: v })
        return parent

    if  ps[1] not in parent[ ps[0] ] or parent[ ps[0] ][ ps[1] ] is None:
        parent[ ps[0] ].update({ps[1]: {}})
    if len(ps) == 3:
        if "array" in parameter_type:
            parent[ ps[0] ][ ps[1] ].update({ps[2]: v.split(',')})
        else:
            parent[ ps[0] ][ ps[1] ].update({ps[2]: v })
        return parent

    if  ps[2] not in parent[ ps[0] ][ ps[1] ] or parent[ ps[0] ][ ps[1] ][ ps[2] ] is None:
        parent[ ps[0] ][ ps[1] ].update({ps[2]: {}})
    if len(ps) == 4:
        if "array" in parameter_type:
            parent[ ps[0] ][ ps[1] ][ ps[2] ].update({ps[3]: v.split(',')})
        else:
            parent[ ps[0] ][ ps[1] ][ ps[2] ].update({ps[3]: v })
        return parent
    
    if len(ps) > 4:
        print("¡¡¡ Parameter key "+dotted_key+" nested too deeply (>4) !!!")
        return '_too_deep_'

    return parent

################################################################################

def get_nested_value(parent, dotted_key, parameter_type="string"):

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
        return '_too_deep_'

    return v

################################################################################
