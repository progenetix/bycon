import re
from cgi_parse import prjsonnice

################################################################################

def check_datatable_delivery(results, byc):

    if not "table" in byc["output"]:
        return
    if not "datatable_mappings" in byc:
        return

    dt_m = byc["datatable_mappings"]
    r_t = byc["response_type"]

    if not byc["response_type"] in dt_m["io_params"]:
        return

    io_params = dt_m["io_params"][ r_t ]
    io_prefixes = dt_m["io_prefixes"][ r_t ]

    print('Content-Type: text/tsv')
    print('Content-Disposition: attachment; filename='+byc["response_type"]+'.tsv')
    print('status: 200')
    print()


    if "idtable" in byc["output"]:
        io_params = {"id": {"db_key":"id", "type": "string" } }
        io_prefixes = {}

    header = create_table_header(io_params, io_prefixes)

    print("\t".join( header ))    
    for pgxdoc in results:
        line = [ ]
        for p, k in io_params.items():
            v = get_nested_value(pgxdoc, k["db_key"])
            if isinstance(v, list):
                line.append("::".join(v))
            else:
                if "integer" in k["type"]:
                    v = int(v)
                line.append(str(v))

        for par, d in io_prefixes.items():

            if "string" in d["type"]:
                if par in pgxdoc:
                    try:
                        line.append(str(pgxdoc[par]["id"]))
                    except:
                        line.append("")
                    try:
                        line.append(str(pgxdoc[par]["label"]))
                    except:
                        line.append("")
                else:
                    line.append("")
                    line.append("")
            elif "array" in d["type"]:
                for pre in d["pres"]:
                    status = False
                    for o in pgxdoc[par]:
                        if pre in o["id"]:
                            try:
                                line.append(str(o["id"]))
                                status = True
                            except:
                                continue
                            try:
                                line.append(str(o["label"]))
                            except:
                                line.append("")
                    if status is False:
                        line.append("")
                        line.append("")
        print("\t".join( line ))

    exit()

################################################################################

def import_datatable_dict_line(byc, parent, fieldnames, line, primary_scope="biosample"):

    io_params = byc["datatable_mappings"]["io_params"][primary_scope]
    io_prefixes = byc["datatable_mappings"]["io_prefixes"][primary_scope]

    pref_array_values = {}
    for f_n in fieldnames:
        v = line[f_n]

        if "___" in f_n:
            par, key, pre = re.match(r"^(\w+)__(\w+)___(\w+)$", f_n).group(1,2,3)
            # TODO: this is a bit complicated - label and id per prefix ...
            if not par in pref_array_values.keys():
                pref_array_values.update({par:{pre:{}}})
            if not pre in pref_array_values[par].keys():
                pref_array_values[par].update({pre:{}})
            pref_array_values[par][pre].update({key:v})
            continue

        if "__" in f_n:
            par, key = re.match(r"^(\w+)__(\w+)$", f_n).group(1,2)
            if par in io_prefixes.keys():
                if not par in parent:
                    parent.update({par:{}})
                parent[par].update({key:v})
            continue
        
        par = f_n

        if par in io_params.keys():
            db_key = io_params[par]["db_key"]
            parameter_type = io_params[par]["type"]

            assign_nested_value(parent, db_key, v, parameter_type="string")

    for l_k, pre_item in pref_array_values.items():
        if not l_k in parent:
            parent.update({l_k:[]})
        for pre, p_v in pre_item.items():
            parent[l_k].append(p_v)


    return parent

################################################################################

def create_table_header(io_params, io_prefixes):

    """podmd
    podmd"""

    header_labs = [ ]

    for par in io_params.keys():
        header_labs.append( par )
    for par, d in io_prefixes.items():
        if "pres" in d:
            for pre in d["pres"]:
                header_labs.append( par+"__id"+"___"+pre )
                header_labs.append( par+"__label"+"___"+pre )
        else:
            header_labs.append( par+"__id" )
            header_labs.append( par+"__label" )

    return header_labs

################################################################################

def assign_nested_value(parent, dotted_key, v, parameter_type="string"):

    if v is None:
        return parent

    if "number" in parameter_type:
        v = 1*v

    ps = dotted_key.split('.')

    if len(ps) == 1:
        if "array" in parameter_type:
            parent.update({ps[0]: [ v ]})
        else:
            parent.update({ps[0]: v })
        return parent

    if not ps[0] in parent:
        parent.update({ps[0]: {}})
    if len(ps) == 2:
        if "array" in parameter_type:
            parent[ ps[0] ].update({ps[1]: [ v ]})
        else:
            parent[ ps[0] ].update({ps[1]: v })
        return parent

    if not ps[1] in parent[ ps[0] ]:
        parent[ ps[0] ].update({ps[1]: {}})
    if len(ps) == 3:
        if "array" in parameter_type:
            parent[ ps[0] ][ ps[1] ].update({ps[2]: [ v ]})
        else:
            parent[ ps[0] ][ ps[1] ].update({ps[2]: v })
        return parent


    if not ps[2] in parent[ ps[0] ][ ps[1] ]:
        parent[ ps[0] ][ ps[1] ].update({ps[2]: {}})
    if len(ps) == 4:
        if "array" in parameter_type:
            parent[ ps[0] ][ ps[1] ][ ps[2] ].update({ps[3]: [ v ]})
        else:
            parent[ ps[0] ][ ps[1] ][ ps[2] ].update({ps[3]: v })
        return parent
    
    if len(ps) > 4:
        print("¡¡¡ Parameter key "+dotted_key+" nested too deeply (>4) !!!")
        return '_too_deep_'

    return parent

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
        return '_too_deep_'

    return v

################################################################################
