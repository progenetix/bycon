import json

########################################################################################################################

def pgx_datapars_from_args(opts, **kwargs):

    data_pars = { }
    data_pars["dataset_id"] = "arraymap"

    for opt, arg in opts:
        if opt in ("-d", "--dataset_id"):
            data_pars[ "dataset_id" ] = arg

    return data_pars

########################################################################################################################

def pgx_queries_from_args(opts, **kwargs):

    queries = { }

    for opt, arg in opts:
        if opt == '-h':
            print('mongoplots.py -b <biocClass> -e <extId>')
            sys.exit( )
        elif opt in ("-j", "--jsonqueries"):
            q_args = json.loads(arg)
            for collname in kwargs[ "config" ][ "dataset_ids" ]:
                if collname in q_args:
                    queries[collname] = q_args[collname]
        else:
            querylist = []
            if opt in ("-b", "--bioclass"):
                querylist.append({"biocharacteristics.type.id": {"$regex": arg } })
            if opt in ("-e", "--extid"):
                querylist.append( { "external_references.type.id": { "$regex": arg } } )
            if len(querylist) > 1:
                queries["biosamples"] = {"$and": querylist }
            elif len(querylist) == 1:
                queries["biosamples"] = querylist[0]

    return queries
