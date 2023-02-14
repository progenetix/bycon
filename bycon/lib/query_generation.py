import cgi, cgitb
import re, yaml
from pymongo import MongoClient
from bson.son import SON

from cgi_parsing import *
from filter_parsing import *
from variant_parsing import *

################################################################################

def initialize_beacon_queries(byc):

    get_filter_flags(byc)
    parse_filters(byc)

    parse_variant_parameters(byc)
    get_variant_request_type(byc)

    generate_queries(byc)
    select_dataset_ids(byc)

    if len(byc["dataset_ids"]) < 1:
        print_text_response("No existing dataset_id - please check dataset_definitions")

    # TODO: HOT FIX
    if "runs" in byc["queries"].keys():
        if not "callsets" in byc["queries"].keys():
            byc["queries"]["callsets"] = byc["queries"].pop("runs")

    return byc

################################################################################

def generate_queries(byc):

    if not "queries" in byc:
        byc.update({"queries": { }})

    _update_queries_from_path_id( byc )
    _update_queries_from_id_values( byc )
    _update_queries_from_cohorts_query(byc)
    _update_queries_from_filters( byc )
    _update_queries_from_variants( byc )
    _update_queries_from_geoquery( byc )
    _update_queries_from_hoid( byc)
    _purge_empty_queries( byc )

    return byc

################################################################################

def _purge_empty_queries( byc ):

    empties = [ ]
    for k, v in byc["queries"].items():
        if not v:
            empties.append( k )
    for e_k in empties:
        byc["queries"].pop(k, None)

    return byc

################################################################################

def replace_queries_in_test_mode(byc):

    if byc["test_mode"] is not True:
        return byc

    try:
        collname = byc["response_entity"]["collection"]
    except:
        return byc

    ret_no = int(byc.get('test_mode_count', 5))

    ds_id = byc["dataset_ids"][0]
    mongo_client = MongoClient()
    data_db = mongo_client[ ds_id ]
    data_collnames = data_db.list_collection_names()

    if not collname in data_collnames:
        return byc

    data_coll = mongo_client[ ds_id ][ collname ]
    rs = list( data_coll.aggregate([{"$sample": {"size":ret_no}}]) )
    _ids = []
    for r in rs:
        _ids.append(r["_id"])

    byc["queries"] = { collname: { "_id": {"$in": _ids } } }

    byc.update( { "empty_query_all_count": data_coll.estimated_document_count() } )

    return byc

################################################################################

def _update_queries_from_path_id( byc ):

    b_mps = byc["beacon_mappings"]

    if "service" in byc["request_path_root"]:
        b_mps = byc["services_mappings"]

    if not byc["request_entity_id"]:
        return byc

    r_e_id = byc["request_entity_id"]
    p_id_v = byc["request_entity_path_id_value"]

    if not byc["request_entity_path_id_value"]:
        return byc

    if not r_e_id in b_mps["response_types"]:
        return byc

    collname = b_mps["response_types"][r_e_id]["collection"]

    if not collname:
        return byc

    byc["queries"].update( { collname: { "id": p_id_v } } )

    return byc

################################################################################

def _update_queries_from_cohorts_query(byc):

    if not "cohorts" in byc["queries"]:
        return byc

    if "cohort" in byc["response_entity_id"]:
        return byc

    c_q = byc["queries"]["cohorts"]

    query = {}
    if "id" in c_q:
        query = {"cohorts.id": c_q["id"]}

    byc["queries"].pop("cohorts", None)

    update_query_for_scope( byc, query, "biosamples")

    return byc

################################################################################

def _update_queries_from_id_values(byc):

    id_f_v = byc["beacon_mappings"]["id_queryscope_mappings"]
    f_d = byc["form_data"]

    this_id_k = byc["response_entity_id"]+"_ids"

    if "ids" in f_d:
        if not this_id_k in f_d:
            f_d.update({this_id_k: f_d["ids"]})

    for id_k, id_s in id_f_v.items():
        q = False
        if id_k in f_d:
            id_v = f_d[id_k]
            if len(id_v) > 1:
                q = {"id":{"$in":id_v}}
            elif len(id_v) == 1:
                q = {"id":id_v[0]}
        if q is not False:
            update_query_for_scope( byc, q, id_s, "AND")

    return byc

################################################################################

def _update_queries_from_hoid( byc):

    if "accessid" in byc["form_data"]:

        accessid = byc["form_data"]["accessid"]
        ho_client = MongoClient()
        ho_db = ho_client[ byc["config"]["info_db"] ]
        ho_coll = ho_db[ byc["config"][ "handover_coll" ] ]
        h_o = ho_coll.find_one( { "id": accessid } )
        
        # accessid overrides ... ?
        if h_o:
            t_k = h_o["target_key"]
            t_v = h_o["target_values"]
            c_n = h_o["target_collection"]
            t_c = h_o["target_count"]

            byc.update({"original_queries": h_o.get("original_queries", None)})

            set_pagination_range(t_c, byc)
            t_v = paginate_list(t_v, byc)

            t_db = h_o["source_db"]
            h_o_q = { t_k: { '$in': t_v } }
            if c_n in byc["queries"]:
                byc["queries"].update( { c_n: { '$and': [ h_o_q, byc["queries"][ c_n ] ] } } )
            else:
                byc["queries"].update( { c_n: h_o_q } )

    return byc

################################################################################

def _update_queries_from_filters(byc):

    """The new version assumes that dataset_id, scope (collection) and field are
    stored in the collation entries. Only filters with exact match to an entry
    in the lookup "collations" collection will be evaluated.
    While the Beacon v2 protocol assumes a logical `AND` between filters, bycon
    has a slightly differing approach:
    * filters against the same field (in the same collection) are treated as
    logical `OR` since this seems logical; and also allows the use of the same
    query object for hierarchical (`child_terms`) query expansion
    * the bycon API allows to pass a `filterLogic` parameter with either `AND`
    (default value) or `OR`
    """

    f_defs = byc["filter_definitions"]
    f_lists = {}

    logic = byc[ "filter_flags" ][ "logic" ]
    f_desc = byc[ "filter_flags" ][ "descendants" ]
    # precision = byc[ "filter_flags" ][ "precision" ]

    mongo_client = MongoClient()
    coll_coll = mongo_client[ byc["config"]["info_db"] ][ byc["config"]["collations_coll"] ]

    filters = byc.get("filters", [])

    for f in filters:

        f_val = f["id"]
        f_desc = f.get("includeDescendantTerms", f_desc)
        f_scope = f.get("scope", False)

        f_info = coll_coll.find_one({"id": f["id"]})
 
        if f_info is None:

            for f_d in f_defs.values():
                f_re = re.compile(f_d["pattern"])
                if f_re.match(f["id"]):
                    if f_d["collationed"] is False:
                        f_info = {
                            "id": f["id"],
                            "scope": f_d["scope"],
                            "db_key": f_d["db_key"],
                            "child_terms": [f["id"]]
                        }
                        f_desc = False

        if f_info is None:
            continue

        f_field = f_info.get("db_key", "id")

        if f_scope is False:
            f_scope = f_info["scope"]

        if f_scope not in byc[ "config" ][ "queried_collections" ]:
            continue

        if f_scope not in f_lists.keys():
            f_lists.update({f_scope:{}})

        if f_field not in f_lists[f_scope].keys():
            f_lists[f_scope].update({f_field:[]})

        if f_desc is True:
            f_lists[f_scope][f_field].extend(f_info["child_terms"])
        else:
            f_lists[f_scope][f_field].append(f_info["id"])

    # creating the queries & combining w/ possible existing ones
    for f_scope in f_lists.keys():
        f_s_l = []
        for f_field, f_queries in f_lists[f_scope].items():
            if len(f_queries) == 1:
                f_s_l.append({ f_field: f_queries[0] })
            else:
                f_s_l.append({ f_field: {"$in": f_queries } })

        if f_scope in byc["queries"]:
            f_s_l.append(byc["queries"][f_scope])

        if len(f_s_l) == 1:
            byc["queries"].update({ f_scope: f_s_l[0] })
        elif len(f_s_l) > 1:
            byc["queries"].update({ f_scope: { logic: f_s_l } })

    return byc

################################################################################

def update_query_for_scope( byc, query, scope, bool_mode="AND"):

    logic = boolean_to_mongo_logic(bool_mode)

    if not scope in byc["queries"]:
        byc["queries"][scope] = query
    else:
        byc["queries"][scope] = { logic: [ byc["queries"][scope], query ] }

    return byc

################################################################################

def _update_queries_from_geoquery( byc ):

    geo_q, geo_pars = geo_query( byc )

    if not geo_q:
        return byc

    update_query_for_scope( byc, geo_q, "biosamples", bool_mode="AND")

    return byc

################################################################################

def _update_queries_from_variants( byc ):

    if not "variant_request_type" in byc:
        return byc

    if not byc["variant_request_type"] in byc["variant_definitions"]["request_types"].keys():
        if not "variants" in byc["queries"]:
            return byc

    if "variantTypeRequest" in byc["variant_request_type"]:
        create_variantTypeRequest_query( byc )
    elif "variantIdRequest" in byc["variant_request_type"]:
        create_variantIdRequest_query( byc )
    elif "variantCNVrequest" in byc["variant_request_type"]:
        create_variantCNVrequest_query( byc )
    elif "variantAlleleRequest" in byc["variant_request_type"]:
        create_variantAlleleRequest_query( byc )
    elif "variantRangeRequest" in byc["variant_request_type"]:
        create_variantRangeRequest_query( byc )
    elif "geneVariantRequest" in byc["variant_request_type"]:
        create_geneVariantRequest_query( byc )
    else:
        return byc

    return byc

################################################################################

def set_pagination_range(d_count, byc):

    r_range = [
        byc["pagination"]["skip"] * byc["pagination"]["limit"],
        byc["pagination"]["skip"] * byc["pagination"]["limit"] + byc["pagination"]["limit"],
    ]

    if byc["pagination"]["skip"] == 0 and byc["pagination"]["limit"] == 0:
        byc["pagination"].update({"range":[0,d_count]})
        return byc

    r_l_i = d_count - 1

    if r_range[0] > r_l_i:
        r_range[0] = r_l_i
    if r_range[-1] > d_count:
        r_range[-1] = d_count

    byc["pagination"].update({"range":r_range})

    return byc

################################################################################

def paginate_list(this, byc):

    if byc["pagination"]["limit"] < 1:
        return this

    r = byc["pagination"]["range"]

    t_no = len(this)
    r_min = r[0] + 1
    r_max = r[-1]

    if r_min > t_no:
        return []
    if r_max > t_no:
        return this[r[0]:r_max]

    return this[r[0]:r[-1]]

################################################################################
################################################################################
################################################################################

def geo_query( byc ):

    geo_q = { }
    geo_pars = { }

    if not "geoloc_definitions" in byc:
        return geo_q, geo_pars

    g_p_defs = byc["geoloc_definitions"]["parameters"]
    g_p_rts = byc["geoloc_definitions"]["request_types"]
    geo_root = byc["geoloc_definitions"]["geo_root"]

    req_type = ""
    # TODO: Make this modular & fix the one_of interpretation to really only 1
    for rt in g_p_rts:
        g_p = { }
        min_p_no = 1
        mat_p_no = 0
        if "all_of" in g_p_rts[ rt ]:
            g_q_k = g_p_rts[ rt ]["all_of"]
            min_p_no = len(g_q_k)
        elif "one_of" in g_p_rts[ rt ]:
            g_q_k = g_p_rts[ rt ]["one_of"]
        else:
            continue

        # print(rt)
        # print(byc["form_data"]["filters"])
        all_p = g_p_rts[ rt ].get("any_of", []) + g_q_k
 
        for g_k in g_p_defs.keys():

            if g_k not in all_p:
                continue

            g_default = None
            if "default" in g_p_defs[ g_k ]:
                g_default = g_p_defs[ g_k ][ "default" ]

            # TODO: This is an ISO lower hack ...

            if g_k.lower() in byc["form_data"]:
                g_v = byc["form_data"][g_k.lower()]
            else:
                g_v = g_default
            if g_v is None:
                continue
            if not re.compile( g_p_defs[ g_k ][ "pattern" ] ).match( str( g_v ) ):
                continue
            if "float" in g_p_defs[ g_k ][ "type" ]:
                g_p[ g_k ] = float(g_v)
            else:
                g_p[ g_k ] = g_v

            if g_k in g_q_k:
                mat_p_no +=1

        if mat_p_no < min_p_no:
            continue

        req_type = rt
        geo_pars = g_p
    

    if "city" in req_type:
        geo_q = return_geo_city_query(geo_root, geo_pars)
        return geo_q, geo_pars

    if "id" in req_type:
        geo_q = { "id": re.compile( geo_pars["id"], re.IGNORECASE ) }
        return geo_q, geo_pars

    if "ISO3166alpha2" in req_type:
        geo_q = { "provenance.geo_location.properties.ISO3166alpha2": byc["form_data"]["iso3166alpha2"].upper() }
    # print(geo_q)
        return geo_q, geo_pars

    if "geoquery" in req_type:
        geoq_l = [ return_geo_longlat_query(geo_root, geo_pars) ]
        for g_k in g_p_rts["geoquery"]["any_of"]:
            if g_k in geo_pars.keys():
                g_v = geo_pars[g_k]
                if len(geo_root) > 0:
                    geopar = ".".join( [geo_root, "properties", g_k] )
                else:
                    geopar = ".".join(["properties", g_k])
                geoq_l.append({ geopar: re.compile( r'^'+str(g_v), re.IGNORECASE ) })

        if len(geoq_l) > 1:
            geo_q = {"$and": geoq_l }
        else:
            geo_q = geoq_l[0]

    return geo_q, geo_pars

################################################################################

def return_geo_city_query(geo_root, geo_pars):

    geoq_l = []

    for g_k, g_v in geo_pars.items():

        if len(geo_root) > 0:
            geopar = ".".join( [geo_root, "properties", g_k] )
        else:
            geopar = ".".join(["properties", g_k])

        geoq_l.append( { geopar: re.compile( r'^'+str(g_v), re.IGNORECASE ) } )

    if len(geoq_l) > 1:
        return {"$and": geoq_l }
    else:
        return geoq_l[0]

################################################################################

def return_geo_longlat_query(geo_root, geo_pars):

    if len(geo_root) > 0:
        geojsonpar = ".".join( (geo_root, "geometry") )
    else:
        geojsonpar = "geo_location.geometry"

    geo_q = {
        geojsonpar: {
            '$near': SON(
                [
                    (
                        '$geometry', SON(
                            [
                                ('type', 'Point'),
                                ('coordinates', [
                                    geo_pars["geo_longitude"],
                                    geo_pars["geo_latitude"]
                                ])
                            ]
                        )
                    ),
                    ('$maxDistance', geo_pars["geo_distance"])
                ]
            )
        }
    }



    return geo_q

