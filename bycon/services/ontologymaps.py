#!/usr/bin/env python3
import re, sys
from os import path
from pymongo import MongoClient

from bycon import *

services_conf_path = path.join( path.dirname( path.abspath(__file__) ), "config" )
services_lib_path = path.join( path.dirname( path.abspath(__file__) ), "lib" )
sys.path.append( services_lib_path )
from service_helpers import *
from service_response_generation import *

"""podmd
* <https://progenetix.org/services/ontologymaps/?filters=NCIT:C3222>
podmd"""

################################################################################
################################################################################
################################################################################

def main():
    try:
        ontologymaps()
    except Exception:
        print_text_response(traceback.format_exc(), 302)
    
################################################################################

def ontologymaps():
    initialize_bycon_service()
    read_service_prefs("ontologymaps", services_conf_path)

    f_d_s = BYC.get("filter_definitions", {})

    r = ByconautServiceResponse()
    p_filter = rest_path_value("ontologymaps")
    if p_filter:
        BYC["BYC_FILTERS"].append({"id": p_filter})

    q_list = [ ]
    q_dups = [ ]
    pre_re = re.compile(r'^(\w+?)([:-].*?)?$')
    for f in BYC["BYC_FILTERS"]:
        f_val = f["id"]
        if pre_re.match( f_val ):
            pre = pre_re.match( f_val ).group(1)

            # TODO TEST
            for f_t, f_d in f_d_s.items():
                if re.compile( f_d["pattern"] ).match( f_val ):
                    if f_val not in q_dups:
                        q_dups.append(f_val)
                        if "start" in BYC_PARS.get("filter_precision", "exact"):
                            q_list.append( { "code_group.id": { "$regex": "^"+f_val } } )
                        elif f["id"] == pre:
                            q_list.append( { "code_group.id": { "$regex": "^"+f_val } } )
                        else:
                            q_list.append( { "code_group.id": f_val } )

    if len(q_list) < 1:
        BYC["ERRORS"].append("No correct filter value provided!")
        BeaconErrorResponse().response(422)

    if len(q_list) > 1:
        query = { '$and': q_list }
    else:
        query = q_list[0]

    c_g = [ ]
    u_c_d = { }
    mongo_client = MongoClient(host=DB_MONGOHOST)
    mongo_coll = mongo_client["progenetix"]["ontologymaps"]
    for o in mongo_coll.find( query, { '_id': False } ):
        for c in o["code_group"]:
            pre, code = re.split("[:-]", c["id"], maxsplit=1)
            u_c_d.update( { c["id"]: { "id": c["id"], "label": c["label"] } } )
        c_g.append( o["code_group"] )

    u_c = [ ]
    for k, u in u_c_d.items():
        u_c.append(u)        
    mongo_client.close( )

    results =  [ { "term_groups": c_g, "unique_terms": u_c } ]
    if "termGroups" in BYC["response_entity_id"]:
        t_g_s = []
        for tg in c_g:
            t_l = []
            for t in tg:
                t_l.append(str(t.get("id", "")))
                t_l.append(str(t.get("label", "")))
            t_g_s.append("\t".join(t_l))

        if "text" in BYC_PARS.get("output", "___none___"):
            print_text_response("\n".join(t_g_s))
        results = c_g

    print_json_response(r.populatedResponse(results))


################################################################################
################################################################################

if __name__ == '__main__':
    main()
