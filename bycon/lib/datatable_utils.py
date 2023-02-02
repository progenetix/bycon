import csv, re, requests
from random import sample as randomSamples
from cgi_parsing import prjsonnice

################################################################################

def read_tsv_to_dictlist(filepath, max_count=0):

    dictlist = []

    with open(filepath, newline='') as csvfile:
    
        data = csv.DictReader(filter(lambda row: row[0]!='#', csvfile), delimiter="\t", quotechar='"')
        fieldnames = list(data.fieldnames)

        for l in data:
            dictlist.append(dict(l))

    if max_count > 0:
        if max_count < len(dictlist):
            dictlist = randomSamples(dictlist, k=max_count)

    return dictlist, fieldnames

################################################################################

def read_www_tsv_to_dictlist(www, max_count=0):

    dictlist = []

    with requests.Session() as s:
        download = s.get(www)
        decoded_content = download.content.decode('utf-8')    
        data = csv.DictReader(filter(lambda row: row[0]!='#', decoded_content.splitlines()), delimiter="\t", quotechar='"')
        fieldnames = list(data.fieldnames)

        for l in data:
            dictlist.append(dict(l))

    if max_count > 0:
        if max_count < len(dictlist):
            dictlist = randomSamples(dictlist, k=max_count)

    return dictlist, fieldnames

################################################################################

def export_datatable_download(results, byc):

    # TODO: separate table generation from HTTP response

    if not "table" in byc["output"]:
        return
    if not "datatable_mappings" in byc:
        return

    dt_m = byc["datatable_mappings"]
    r_t = byc["response_entity_id"]

    if not byc["response_entity_id"] in dt_m["io_params"]:
        return

    io_params = dt_m["io_params"][ r_t ]
    io_prefixes = dt_m["io_prefixes"][ r_t ]

    if not "local" in byc["env"]:
        print('Content-Type: text/tsv')
        if byc["download_mode"] is True:
            print('Content-Disposition: attachment; filename='+byc["response_entity_id"]+'.tsv')
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
            t = k.get("type", "string")
            v = get_nested_value(pgxdoc, k["db_key"])
            if isinstance(v, list):
                line.append("::".join(v))
            else:
                if "integer" in t:
                    v = int(v)
                line.append(str(v))

        for par, d in io_prefixes.items():

            t = k.get("type", "string")
            if "string" in t:
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
            elif "array" in t:
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

def import_datatable_dict_line(byc, parent, fieldnames, lineobj, primary_scope="biosample"):

    io_params = byc["datatable_mappings"]["io_params"][primary_scope]
    io_prefixes = byc["datatable_mappings"]["io_prefixes"][primary_scope]

    ios = list(io_params.keys()) + list(io_prefixes.keys())

    pref_array_values = {}

    for f_n in fieldnames:

        if "#"in f_n:
            continue

        if f_n not in ios:
            continue

        v = lineobj[f_n].strip()

        if len(v) < 1:
            if f_n in io_params.keys():
                v = io_params[f_n].get("default", "")

        if len(v) < 1:
            continue

        if "__delete__" in v.lower():
            v = ""

        if "___" in f_n:
            par, key, pre = re.match(r"^(\w+)__(\w+)___(\w+)$", f_n).group(1,2,3)
            # TODO: this is a bit complicated - label and id per prefix ...
            if not par in pref_array_values.keys():
                pref_array_values.update({par:{pre:{}}})
            if not pre in pref_array_values[par].keys():
                pref_array_values[par].update({pre:{}})
            pref_array_values[par][pre].update({key:v})
            continue
        
        par = f_n

        if par in io_params.keys():
            db_key = io_params[par]["db_key"]
            parameter_type = io_params[par].get("type", "string")

            assign_nested_value(parent, db_key, v, parameter_type)

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
            for pre in d["pres"].keys():
                header_labs.append( par+"_id"+"___"+pre )
                header_labs.append( par+"_label"+"___"+pre )

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
            parent.update({ps[0]: v.split(',')})
        else:
            parent.update({ps[0]: v })
        return parent

    if not ps[0] in parent:
        parent.update({ps[0]: {}})
    if len(ps) == 2:
        if "array" in parameter_type:
            parent[ ps[0] ].update({ps[1]: v.split(',')})
        else:
            parent[ ps[0] ].update({ps[1]: v })
        return parent

    if not ps[1] in parent[ ps[0] ]:
        parent[ ps[0] ].update({ps[1]: {}})
    if len(ps) == 3:
        if "array" in parameter_type:
            parent[ ps[0] ][ ps[1] ].update({ps[2]: v.split(',')})
        else:
            parent[ ps[0] ][ ps[1] ].update({ps[2]: v })
        return parent


    if not ps[2] in parent[ ps[0] ][ ps[1] ]:
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
