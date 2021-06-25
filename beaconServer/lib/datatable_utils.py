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
    header = create_table_header(io_params, io_prefixes)

    print("\t".join( header ))    
    for pgxdoc in byc["service_response"]["result_sets"][0]["results"]:
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
                    line.append(str(pgxdoc[par]["id"]))
                    if "label" in pgxdoc[par]:
                        line.append(str(pgxdoc[par]["label"]))
                    else:
                        line.append("")
                else:
                    line.append("")
                    line.append("")
            elif "array" in d["type"]:
                for pre in d["pres"]:
                    status = False
                    for o in pgxdoc[par]:
                        if pre in o["id"]:
                            line.append(str(o["id"]))
                            status = True
                            if "label" in o:
                                line.append(str(o["label"]))
                            else:
                                line.append("")
                    if status is False:
                        line.append("")
                        line.append("")
        print("\t".join( line ))

    exit()

################################################################################

def create_table_header(params, prefixes):

    """podmd
    podmd"""

    header_labs = [ ]

    for par in params.keys():
        header_labs.append( par )
    for par in prefixes:
        for pre in prefixes[par]:
            header_labs.append( pre+"::id" )
            header_labs.append( pre+"::label" )

    return header_labs

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
