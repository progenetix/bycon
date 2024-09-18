import csv, re, requests
# from attrdictionary import AttrDict
from random import sample as randomSamples

# bycon
from bycon import RefactoredValues, prdbug, prdlhead, prjsonnice, BYC, BYC_PARS, ENV

################################################################################

def export_datatable_download(results):
    # TODO: separate table generation from HTTP response
    dt_m = BYC["datatable_mappings"]
    r_t = BYC.get("response_entity_id", "___none___")
    if not r_t in dt_m["definitions"]:
        return
    sel_pars = BYC_PARS.get("delivery_keys", [])
    io_params = dt_m["definitions"][ r_t ]["parameters"]
    if len(sel_pars) > 0:
        io_params = { k: v for k, v in io_params.items() if k in sel_pars }
    prdlhead(f'{r_t}.tsv')
    header = create_table_header(io_params)
    print("\t".join( header ))

    for pgxdoc in results:
        line = [ ]
        for par, par_defs in io_params.items():
            parameter_type = par_defs.get("type", "string")
            db_key = par_defs.get("db_key", "___undefined___")
            v = get_nested_value(pgxdoc, db_key)
            if isinstance(v, list):
                line.append("::".join(map(str, (v))))
            else:
                line.append(str(v))
        print("\t".join( line ))

    exit()


################################################################################

def import_datatable_dict_line(parent, fieldnames, lineobj, primary_scope="biosample"):
    dt_m = BYC["datatable_mappings"]
    if not primary_scope in dt_m["definitions"]:
        return
    io_params = dt_m["definitions"][ primary_scope ]["parameters"]
    def_params = create_table_header(io_params)
    for f_n in fieldnames:
        if "#"in f_n:
            continue
        if f_n not in def_params:
            continue
        if not (par_defs := io_params.get(f_n, {})):
            continue
        if not (dotted_key := par_defs.get("db_key")):
            continue
        p_type = par_defs.get("type", "string")

        v = lineobj[f_n].strip()
        if v.lower() in (".", "na"):
            v = ""
        if len(v) < 1:
            if f_n in io_params.keys():
                v = io_params[f_n].get("default", "")
        if len(v) < 1:
            continue

        # this makes only sense for updating existing data; if there would be
        # no value, the parameter would just be excluded from the update object
        # if there was an empy value
        if v.lower() in ("___delete___", "__delete__", "none", "___none___", "__none__", "-"):
            if "array" in p_type:
                v = []
            elif "object" in p_type:
                v = {}
            else:
                v = ""
        else:
            v = RefactoredValues(par_defs).refVal(v.split(","))

        assign_nested_value(parent, dotted_key, v, par_defs)

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

def assign_nested_value(parent, dotted_key, v, parameter_definitions={}):
    parameter_type = parameter_definitions.get("type", "string")

    if not v and v != 0:
        if not (v := parameter_definitions.get("default")):
            return parent

    if "array" in parameter_type:
        if type(v) is not list:
            v = v.split(',')
    elif "num" in parameter_type:
        if str(v).strip().lstrip('-').replace('.','',1).isdigit():
            v = float(v)
    elif "integer" in parameter_type:
        if str(v).strip().isdigit():
            v = int(v)
    elif "string" in parameter_type:
        v = str(v)

    ps = dotted_key.split('.')

    if len(ps) == 1:
        parent.update({ps[0]: v })
        return parent

    if ps[0] not in parent or parent[ ps[0] ] is None:
        parent.update({ps[0]: {}})
    if len(ps) == 2:
        parent[ ps[0] ].update({ps[1]: v })
        return parent
    if  ps[1] not in parent[ ps[0] ] or parent[ ps[0] ][ ps[1] ] is None:
        parent[ ps[0] ].update({ps[1]: {}})
    if len(ps) == 3:
        parent[ ps[0] ][ ps[1] ].update({ps[2]: v })
        return parent
    if  ps[2] not in parent[ ps[0] ][ ps[1] ] or parent[ ps[0] ][ ps[1] ][ ps[2] ] is None:
        parent[ ps[0] ][ ps[1] ].update({ps[2]: {}})
    if len(ps) == 4:
        parent[ ps[0] ][ ps[1] ][ ps[2] ].update({ps[3]: v })
        return parent
    
    if len(ps) > 4:
        print("¡¡¡ Parameter key "+dotted_key+" nested too deeply (>4) !!!")
        return '_too_deep_'

    return parent

################################################################################

def get_nested_value(parent, dotted_key, parameter_type="string"):
    ps = str(dotted_key).split('.')
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
