from bycon import *
from byconServiceLibs import ByconMap, ByconServiceResponse, open_text_streaming, ByconGeolocs

def geolocations():
    """
    ==TBD==

    #### Examples

    * <https://progenetix.org/services/geolocations?city=zurich>
    * <https://progenetix.org/services/geolocations?geoLongitude=8.55&geoLatitude=47.37&geoDistance=100000>
    * <https://progenetix.org/services/geolocations?geoLongitude=8.55&geoLatitude=47.37&geoDistance=100000&output=map>
    * <http://progenetix.org/services/geolocations?inputfile=https://raw.githubusercontent.com/progenetix/pgxMaps/main/rsrc/locationtest.tsv&debug=&output=map&>
    * <http://progenetix.org/cgi/bycon/services/geolocations.py?city=New&ISO3166alpha2=UK&output=map&markerType=marker>
    """
    # TODO: make the input parsing a class
    GEOL = ByconGeolocs()
    if "inputfile" in BYC_PARS:
        results = GEOL.get_locations_from_web()
    else:
        query = GeoQuery().get_geoquery()
        if not query:
            BYC["ERRORS"].append("No query generated - missing or malformed parameters")
        else:
            results = mongo_result_list(SERVICES_DB, GEOLOCS_COLL, query, { '_id': False } )

    BeaconErrorResponse().respond_if_errors()

    if "map" in str(BYC_PARS.get("plot_type", "___none___")):
        BM = ByconMap()
        BM.add_data_from_results_list(results)
        BM.printMapHTML()

    if len(results) == 1:
        if (gd := BYC_PARS.get("geo_distance")):
            l_l = results[0]["geo_location"]["geometry"]["coordinates"]
            BYC_PARS.update({
                "geo_longitude": l_l[0],
                "geo_latitude": l_l[1],
                "geo_distance": int(gd)
            })
            prdbug(results)
            query = GeoQuery().get_geoquery()
            results = mongo_result_list(SERVICES_DB, GEOLOCS_COLL, query, { '_id': False } )

    BeaconErrorResponse().respond_if_errors()

    __export_geotable(results)
    ByconServiceResponse().print_populated_response(results)


################################################################################

def __export_geotable(results):
    if not "text" in BYC_PARS.get("output", "___none___"):
        return

    open_text_streaming("geolocations.tsv")
    for g in results:
        s_comps = []
        for k in ["city", "country", "continent"]:
            s_comps.append(str(g["geo_location"]["properties"].get(k, "")))
        s_comps.append(str(g.get("id", "")))
        for l in g["geo_location"]["geometry"].get("coordinates", [0,0]):
            s_comps.append(str(l))
        print("\t".join(s_comps))
    exit()


################################################################################
################################################################################

if __name__ == '__main__':
    main()
