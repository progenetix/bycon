import re
from os import environ, path, pardir
from pymongo import MongoClient
from operator import itemgetter

from bycon import (
    BYC,
    BYC_PARS,
    BeaconErrorResponse,
    ByconFilters,
    DB_MONGOHOST,
    GeoQuery,
    prdbug
)
from byconServiceLibs import ByconMap, ByconServiceResponse, read_service_prefs

services_conf_path = path.join( path.dirname( path.abspath(__file__) ), "config" )

################################################################################

# TODO: rewrite with class, use of standard filter query etc.

def publications():
    """
    The _publications_ service provides API functionality for accessing the
    Progenetix [publications](http://progenetix.org/publications/) collection, which
    represents curated information about several thousand articles reporting
    genome-wide screening experiments in cancer. 

    #### Examples

    * <https://progenetix.org/services/publications/?filters=pubmed>
    * <http://progenetix.org/services/publications/?filters=pubmed,genomes:&gt;200,arraymap:&gt;1>
    * <http://progenetix.org/services/publications/?filters=pubmed:22824167&method=details>
    * <http://progenetix.org/services/publications/?geoLongitude=8.55&geoLatitude=47.37&geoDistance=100000>
    """

    # The `publications.yaml` file contains an override for `filter_definitions`
    read_service_prefs("publications", services_conf_path)
    f_d_s = BYC["filter_definitions"].get("$defs", {})

    query = __create_filters_query()
    geo_q = GeoQuery().get_geoquery()

    if geo_q:
        if len(query.keys()) < 1:
            query = geo_q
        else:
            query = { '$and': [ geo_q, query ] }
    if len(query.keys()) < 1:
        BYC["ERRORS"].append("No query could be constructed from the parameters provided.")
    
    BeaconErrorResponse().respond_if_errors()

    mongo_client = MongoClient(host=DB_MONGOHOST)
    pub_coll = mongo_client[ "_byconServicesDB" ][ "publications" ]
    p_re = re.compile( f_d_s["pubmed"]["pattern"] )
    d_k = BYC_PARS.get("delivery_keys", [])
    p_l = []

    prdbug(f'query: {query}')

    for pub in pub_coll.find( query, { "_id": 0 } ):
        # prdbug(f'pub: {pub}')
        s = { }
        if len(d_k) < 1:
            s = pub
        else:
            for k in d_k:
                # TODO: harmless but ugly hack
                if k in pub.keys():
                    if k == "counts":
                        s[ k ] = { }
                        for c in pub[ k ]:
                            if pub[ k ][ c ]:
                                try:
                                    s[ k ][ c ] = int(float(pub[ k ][ c ]))
                                except:
                                    s[ k ][ c ] = 0
                            else:
                                s[ k ][ c ] = 0
                    else:
                        s[ k ] = pub[ k ]
                else:
                    s[ k ] = None
        try:
            s_v = p_re.match(s[ "id" ]).group(3)
            s[ "sortid" ] = int(s_v)
        except:
            s[ "sortid" ] = -1

        p_l.append( s )

    mongo_client.close( )
    results = sorted(p_l, key=itemgetter('sortid'), reverse = True)
    __check_publications_map_response(results)
    ByconServiceResponse().print_populated_response(results)


################################################################################
################################################################################

def __check_publications_map_response(results):
    if not "map" in str(BYC_PARS.get("plot_type", "___none___")):
        return

    u_locs = {}
    for p in results:
        counts = p.get("counts", {})
        geoloc = p.get("geo_location", None)
        if not geoloc:
            pass
        l_k = "{}::{}".format(geoloc["geometry"]["coordinates"][1], geoloc["geometry"]["coordinates"][0])

        if not l_k in u_locs.keys():
            u_locs.update({l_k:{"geo_location": geoloc}})
            u_locs[l_k]["geo_location"]["properties"].update({"items":[]})

        m_c = counts.get("genomes", 0)
        m_s = u_locs[l_k]["geo_location"]["properties"].get("marker_count", 0) + m_c

        # the link here has to be in double quotes since it is then enclosed in
        # single quotes in the HTML
        link = f'<a href="/publication/?id={p["id"]}">{p["id"]}</a> ({int(m_c)})'
        # link = f'{p["id"]} ({int(m_c)})'    #  ({m_c})
        u_locs[l_k]["geo_location"]["properties"].update({"marker_count":m_s})
        u_locs[l_k]["geo_location"]["properties"]["items"].append(link)
    geolocs = u_locs.values()

    BM = ByconMap()
    BM.add_data_from_results_list(geolocs)
    BM.printMapHTML()


################################################################################

def __create_filters_query():
    filters = ByconFilters().get_filters()
    filter_precision = BYC_PARS.get("filter_precision", "exact")
    f_d_s = BYC["filter_definitions"].get("$defs", {})
    query = { }
    error = ""

    if BYC["TEST_MODE"] is True:
        test_mode_count = int(BYC_PARS.get('test_mode_count', 5))
        mongo_client = MongoClient(host=DB_MONGOHOST)
        data_coll = mongo_client[ "_byconServicesDB" ][ "publications" ]

        rs = list(data_coll.aggregate([{"$sample": {"size": test_mode_count}}]))
        query = {"_id": {"$in": list(s["_id"] for s in rs)}}
        return query, error

    q_list = [ ]
    count_pat = re.compile( r'^(\w+?)\:([>=<])(\d+?)$' )

    fds_pres = list(f_d_s.keys())

    for f in filters:
        f_val = f.get("id", "")
        prdbug(f_val)
        if len(f_val) < 1:
            continue
        pre_code = re.split('-|:', f_val)
        pre = pre_code[0]
        prk = pre
        if "pubmed" in pre:
           prk = "pubmed" 

        if str(prk) not in f_d_s.keys():
            continue

        dbk = f_d_s[ prk ]["db_key"]

        if count_pat.match( f_val ):
            pre, op, no = count_pat.match(f_val).group(1,2,3)
            # dbk = f_d_s[ pre ][ "db_key" ]
            if op == ">":
                op = '$gt'
            elif op == "<":
                op = '$lt'
            elif op == "=":
                op = '$eq'
            else:
                BYC["ERRORS"].append(f'uncaught filter error: {f_val}')
                continue
            q_list.append( { dbk: { op: int(no) } } )
        elif "start" in filter_precision or len(pre_code) == 1:
            """
            If there was only prefix a regex match is enforced - basically here
            for the selection of pubmed labeled publications.
            """
            q_list.append( { "id": re.compile(r'^'+f_val ) } )
        elif "pgxuse" in f_val:
            if ":y" in f_val.lower():
                q_list.append( { dbk: {"$regex":"y"} } )
        else:
            q_list.append( { dbk: f_val } )

    if len(q_list) > 1:
        query = { '$and': q_list }
    elif len(q_list) < 1:
        query = {}
    else:
        query = q_list[0]

    prdbug(f'filters query: {query}')

    return query
