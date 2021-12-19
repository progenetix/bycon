def export_datatable(byc):

    if not "table" in byc["output"]:
        return
    if not "datatable_mappings" in byc:
        return
    if not byc["response_type"] in byc["datatable_mappings"]["io_params"]:
        return

    print('Content-Type: text/tsv')
    print('Content-Disposition: attachment; filename='+byc["response_type"]+'.tsv')
    print('status: 200')
    print()

    io_params = byc["datatable_mappings"]["io_params"][ byc["response_type"] ]
    io_prefixes = byc["datatable_mappings"]["io_prefixes"][ byc["response_type"] ]

    if "idtable" in byc["output"]:
        io_params = {"id": {"db_key":"id", "type": "string" } }
        io_prefixes = {}

    header = create_table_header(io_params, io_prefixes)

    print("\t".join( header ))    
    for pgxdoc in byc["service_response"]["response"]["result_sets"][0]["results"]:
        line = [ ]
        for p, k in io_params.items():
            v = _get_nested_value(pgxdoc, k["db_key"])
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

def create_table_header(io_params, io_prefixes):

    """podmd
    podmd"""

    header_labs = [ ]

    for par in io_params.keys():
        header_labs.append( par )
    for par, d in io_prefixes.items():
        if "pres" in d:
            for pre in d["pres"]:
                header_labs.append( par+"::id"+"___"+pre )
                header_labs.append( par+"::label"+"___"+pre )
        else:
            header_labs.append( par+"::id" )
            header_labs.append( par+"::label" )

    return header_labs

################################################################################

def assign_nested_value(parent, dotted_key, v, parameter_type="string"):

    if v is None:
        return parent

    ps = dotted_key.split('.')

    if len(ps) == 1:
        if "array" in parameter_type:
            parent.update({ps[0]: [ v ]})
        else:
            if len(v) > 0:
                parent.update({ps[0]: v })
    elif len(ps) == 2:
        if "array" in parameter_type:
            parent[ ps[0] ].update({ps[1]: [ v ]})
        else:
            if len(v) > 0:
                parent[ ps[0] ].update({ps[1]: v })
    elif len(ps) == 3:
        if "array" in parameter_type:
            parent[ ps[0] ][ ps[1] ].update({ps[2]: [ v ]})
        else:
            if len(v) > 0:
                parent[ ps[0] ][ ps[1] ].update({ps[2]: v })
    elif len(ps) == 4:
        if "array" in parameter_type:
            parent[ ps[0] ][ ps[1] ][ ps[2] ].update({ps[3]: [ v ]})
        else:
            if len(v) > 0:
                parent[ ps[0] ][ ps[1] ][ ps[2] ].update({ps[3]: v })
    elif len(ps) > 4:
        print("¡¡¡ Parameter key "+dotted_key+" nested too deeply (>4) !!!")
        return '_too_deep_'

    return parent

################################################################################

################################################################################

def _get_nested_value(parent, dotted_key):

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
