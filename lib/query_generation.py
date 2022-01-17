import cgi, cgitb
import re, yaml
from pymongo import MongoClient
from bson.son import SON

from parse_variants import *
from parse_filters import *

################################################################################

def initialize_beacon_queries(byc):

    get_filter_flags(byc)
    parse_filters(byc)

    parse_variants(byc)
    get_variant_request_type(byc)

    generate_queries(byc)

    select_dataset_ids(byc)
    check_dataset_ids(byc)

    # TODO: HOT FIX
    if "runs" in byc["queries"].keys():
        if not "callsets" in byc["queries"].keys():
            byc["queries"]["callsets"] = byc["queries"].pop("runs")

    return byc

################################################################################

def generate_queries(byc):

    if not "queries" in byc:
        byc.update({"queries": { }})

    update_queries_from_path_id( byc )
    update_queries_from_id_values( byc )
    update_queries_from_filters( byc )
    update_queries_from_hoid( byc)
    update_queries_from_variants( byc )
    update_queries_from_endpoints( byc )
    update_queries_from_geoquery( byc )
    purge_empty_queries( byc )

    return byc

################################################################################

def purge_empty_queries( byc ):

    empties = [ ]
    for k, v in byc["queries"].items():
        if not v:
            empties.append( k )
    for e_k in empties:
        del( byc["queries"][ k ] )

    return byc

################################################################################

def generate_empty_query_items_request(ds_id, byc, ret_no=10):

    # This is called separately, only for specific collections

    collname = byc["response_entity"]["collection"]

    if byc["empty_query_all_response"] is False:
        return byc

    mongo_client = MongoClient()
    data_db = mongo_client[ ds_id ]
    data_coll = mongo_client[ ds_id ][ collname ]

    rs = list( data_coll.aggregate([{"$sample": {"size":ret_no}}]) )
    _ids = []
    for r in rs:
        _ids.append(r["_id"])

    byc["queries"].update( { collname: { "_id": {"$in": _ids } } } )

    byc.update( { "empty_query_all_count": data_coll.estimated_document_count() } )

    return byc

################################################################################

def update_queries_from_path_id( byc ):

    dummy_id_patterns = ["_id_", "__id__", "___id___", "_test_", "__test__", "___test___", r'{id}' ]

    if not environ.get('REQUEST_URI'):
        return byc

    url_comps = urlparse( environ.get('REQUEST_URI') )

    if "service_name" in byc:
        pgx_base = byc["service_name"]

    rb_t = rest_path_value("beacon")

    if not rb_t == pgx_base:
        if not rb_t in byc["beacon_base_paths"]:
            return byc

    byc.update({"response_type": _get_response_type_from_path(rb_t, byc) })

    p_id = rest_path_value(rb_t)

    # TODO: prototyping here ...
    if p_id == "filteringTerms":
        byc.update({"response_type": "filteringTerm" })
        byc["form_data"].update({"scope": rb_t })
        return byc

    if p_id:
        if not "empty_value" in p_id:
            s_id = p_id
            if s_id in dummy_id_patterns:
                if "defaults" in byc["this_config"]:
                    s_id = byc["this_config"]["defaults"].get("test_document_id", "")

            byc.update({ "id_from_path": s_id })

            byc["queries"].update(
                { pgx_base: { "id": s_id } } )

            # That's why the original path id was kept...
            r_t = rest_path_value(p_id)
            if not "empty_value" in r_t:
                byc.update({"response_type": _get_response_type_from_path(r_t, byc) })

    return byc

################################################################################

def _get_response_type_from_path(path_element, byc):

    try:
        t = byc["beacon_mappings"]["path_response_type_mappings"][path_element]
        for r_d in byc["beacon_mappings"]["response_types"]:
            if r_d["entity_type"] == t:
                path_element = r_d["entity_type"]
    except:
        pass

    return path_element

################################################################################

def update_queries_from_id_values(byc):

    id_re = re.compile(r'^\w[\w\-]+?\w$')

    for par, scope in byc["config"]["id_query_map"].items():
        if par in byc["form_data"]:
            q_list = [ ]
            q = False
            for id_v in byc["form_data"][par]:
                if id_re.match(id_v):
                    q_list.append({"id":id_v})
            if len(q_list) == 1:
                q = q_list[0]
            elif len(q_list) > 1:
                q = { '$or': q_list }
            if q:
                if scope in byc["queries"]:
                    byc["queries"].update( { scope: { '$and': [ q, byc["queries"][ scope ] ] } } )
                else:
                    byc["queries"].update( { scope: q } )

    return byc

################################################################################

def update_queries_from_hoid( byc):

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
            t_db = h_o["source_db"]
            h_o_q = { t_k: { '$in': t_v } }
            if c_n in byc["queries"]:
                byc["queries"].update( { c_n: { '$and': [ h_o_q, byc["queries"][ c_n ] ] } } )
            else:
                byc["queries"].update( { c_n: h_o_q } )

    return byc

################################################################################

def update_queries_from_filters(byc):

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

    filter_lists = {}

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
            continue

        f_field = f_info.get("db_key", "id")

        if f_scope is False:
            f_scope = f_info["scope"]

        if f_scope not in byc[ "config" ][ "collections" ]:
            continue

        if f_scope not in filter_lists.keys():
            filter_lists.update({f_scope:{}})
        if f_field not in filter_lists[f_scope].keys():
            filter_lists[f_scope].update({f_field:[]})

        if f_desc is True:
            filter_lists[f_scope][f_field].extend(f_info["child_terms"])
        else:
            filter_lists[f_scope][f_field].append(f_info["id"])

    # creating the queries & combining w/ possible existing ones
    for f_scope in filter_lists.keys():
        f_s_l = []
        for f_field, f_queries in filter_lists[f_scope].items():
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

def update_queries_from_endpoints( byc ):

    if not "endpoint_pars" in byc:
        return byc

    if len(byc["endpoint_pars"]) < 1:
        return byc

    for c_n in byc["endpoint_pars"]["queries"].keys():
        epq = byc["endpoint_pars"]["queries"][c_n]
        if c_n in byc["queries"]:
            byc["queries"][c_n] = { '$and': [ epq, byc["queries"][c_n] ] }
        else:
            byc["queries"][c_n] = epq

    return byc

################################################################################

def update_queries_from_geoquery( byc ):

    geo_q, geo_pars = geo_query( byc )

    if not geo_q:
        return byc

    if not "biosamples" in byc["queries"]:
        byc["queries"]["biosamples"] = geo_q
    else:
        byc["queries"]["biosamples"] = { '$and': [ geo_q, byc["queries"]["biosamples"] ] }

    return byc

################################################################################

def update_queries_from_variants( byc ):

    if not "variant_request_type" in byc:
        return byc

    if not byc["variant_request_type"] in byc["variant_definitions"]["request_types"].keys():
        if not "variants" in byc["queries"]:
            return byc

    # v_q_method = "create_"+byc["variant_request_type"]+"_query"

    if "variantIdRequest" in byc["variant_request_type"]:
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
    for rt in g_p_rts:
        g_p = { }
        g_q_k = g_p_rts[ rt ]["all_of"]
        for g_k in g_q_k:
            g_default = None
            if "default" in g_p_defs[ g_k ]:
                g_default = g_p_defs[ g_k ][ "default" ]
            if g_k in byc["form_data"]:
                g_v = byc["form_data"][g_k]
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

        if len( g_p ) < len( g_q_k ):
            continue

        req_type = rt
        geo_pars = g_p

    if "city" in req_type:
        geo_q = return_geo_city_query(geo_root, geo_pars)

    if "id" in req_type:
        geo_q = { "id": re.compile( geo_pars["id"], re.IGNORECASE ) }

    if "geoquery" in req_type:
        geo_q = return_geo_longlat_query(geo_root, geo_pars)



    return geo_q, geo_pars

################################################################################

def return_geo_city_query(geo_root, geo_pars):

    if len(geo_root) > 0:
        citypar = ".".join( (geo_root, "properties", "city") )
    else:
        citypar = "properties.city"

    geo_q = { citypar: re.compile( r'^'+geo_pars["city"], re.IGNORECASE ) }

    return geo_q

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
                                    geo_pars["geolongitude"],
                                    geo_pars["geolatitude"]
                                ])
                            ]
                        )
                    ),
                    ('$maxDistance', geo_pars["geodistance"])
                ]
            )
        }
    }

    return geo_q

################################################################################

