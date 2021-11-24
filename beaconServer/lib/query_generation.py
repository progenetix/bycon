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

    p_id = rest_path_value(rb_t)

    if p_id:
        if not "empty_value" in p_id:
            s_id = p_id
            if s_id in dummy_id_patterns:
                if "defaults" in byc["this_config"]:
                    s_id = byc["this_config"]["defaults"].get("test_document_id", "")

            byc.update({ "id_from_path": s_id })
            byc["queries"].update(
                { pgx_base: { "id": s_id } } )
            if not "response_types" in byc["this_config"]:
                return byc

            # That's why the original path id was kept...
            r_t = rest_path_value(p_id)

            try:
                t = byc["beacon_mappings"]["path_response_type_mappings"][r_t]
                for r_d in byc["beacon_mappings"]["response_types"]:
                    if r_d["entity_type"] == t:
                        byc.update({"response_type": r_d["entity_type"]})
            except:
                pass

    return byc


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

def update_queries_from_filters( byc ):

    """podmd

    #### `update_queries_from_filters`

    This method creates a query object (dictionary) with entries for each of the
    standard data collections.

    Filter values are not checked for their correct syntax; this should have
    happened in a pre-parsing step and allows to use the method with non-standard
    values, e.g. to fix erroneous database entries.
    
    podmd"""
        
    query_lists = { }

    logic = byc[ "filter_flags" ][ "logic" ]
    precision = byc[ "filter_flags" ][ "precision" ]

    for c_n in byc[ "config" ][ "collections" ]:
        query_lists[c_n] = [ ]
        if c_n in byc["queries"]:
            query_lists[c_n].append( byc["queries"][c_n] )
 
    mongo_client = MongoClient()

    filters = byc.get("filters", {})
    for f in filters:
        f_val = f["id"]
        f_desc = f.get("includeDescendantTerms", True)
        f_scope = f.get("scope", False)
        pre_code = re.split('-|:', f_val)
        pre = pre_code[0]
        if pre in byc["filter_definitions"]:
            pre_defs = byc["filter_definitions"][pre]
            if "remove" in pre_defs:
                f_val = re.sub(pre_defs["remove"], "", f_val)
                pre = re.sub(pre_defs["remove"], "", pre)

            if f_scope is False:
                f_scope = pre_defs["scopes"][0]

            if f_scope not in query_lists.keys():
                continue

            if "start" in precision or len(pre_code) == 1:
                query_lists[ f_scope ].append( { pre_defs[ "db_key" ]: { "$regex": "^"+f_val } } )
                break
            else:
                q_keys = { f_val: 1 }

                """podmd

                The Beacon query paradigm assumes a logical 'AND'
                between different filters. Also, it assumes that a
                query against a hierarchical term will also retrieve
                matches to its child terms. These two paradigms are
                incompatible if the targets don't store all their
                hierarchies with them.
                To resolve queries to include all child terms the 
                current solution is to perform a look up query for
                the current filter term, in the `collations` database,
                and create an 'OR' query which replaces the single
                filter value (if more than one term).
                
                podmd"""
                if f_desc is True:
                    for ds_id in byc["dataset_ids"]:
                        mongo_coll = mongo_client[ ds_id ][ "collations" ]
                        try:
                            f_def = mongo_coll.find_one( { "id": f_val })
                            if "child_terms" in f_def:
                                for c in f_def["child_terms"]:
                                    if pre in c:
                                        q_keys.update({c:1})
                        except:
                            pass

                if len(q_keys.keys()) == 1:
                    query_lists[ f_scope ].append( { pre_defs[ "db_key" ]: f_val } )
                else:
                    f_q_l = [ ]
                    for f_c in q_keys.keys():
                        f_q_l.append( { pre_defs[ "db_key" ]: f_c } )
                    query_lists[ f_scope ].append( { '$or': f_q_l } )
                break
                        
    mongo_client.close()

    for c_n in byc[ "config" ][ "collections" ]:
        if len(query_lists[c_n]) == 1:
            byc["queries"][ c_n ] = query_lists[c_n][0]
        elif len( query_lists[c_n] ) > 1:
            byc["queries"][ c_n ] = { logic: query_lists[c_n] }

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

