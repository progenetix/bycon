import re
from os import environ
from pymongo import MongoClient, GEOSPHERE

from bycon import BYC, DB_MONGOHOST

################################################################################

def mongodb_update_indexes(ds_id):
    dt_m = BYC["datatable_mappings"]
    s_c = BYC.get("service_config", {})
    b_rt_s = s_c["indexed_response_types"]
    mongo_client = MongoClient(host=DB_MONGOHOST)
    data_db = mongo_client[ds_id]
    coll_names = data_db.list_collection_names()
    for r_t, r_d in b_rt_s.items():
        collname = r_d.get("collection", False)
        if collname not in coll_names:
            print(f"¡¡¡ Collection {collname} does not exist in {ds_id} !!!")
            continue
        i_coll = data_db[ collname ]
        io_params = dt_m["definitions"][ r_t ]["parameters"]

        for p_k, p_v in io_params.items():
            if (i_t := p_v.get("indexed", False)) is False:
                continue

            if (k := p_v.get("db_key")):
                if (i_d := p_v.get("items")):
                    if (i_d_i := i_d.get("indexed")):
                        for i_p in i_d_i:
                            i_k = f'{k}.{i_p}'
                            print(f'Creating index "{i_k}" in {collname} from {ds_id}')
                            i_m = i_coll.create_index(i_k)
                            print(i_m)
                    continue
                print(f'Creating index "{k}" in {collname} from {ds_id}')
                m = i_coll.create_index(k)
                print(m)

        # TODO: 

        # if "geoprov_lat" in io_params.keys():
        #     k = re.sub("properties.latitude", "geometry", io_params["geoprov_lat"]["db_key"])
        #     m = i_coll.create_index([(k, GEOSPHERE)])
        #     print(m)

    #<------------------------ special collections --------------------------->#

    special_colls = s_c.get("indexed_special_collections", {})
    __index_by_colldef(ds_id, special_colls)

    #<------------------------- special databases ---------------------------->#

    for s_db, coll_defs in s_c.get("indexed_special_dbs", {}).items():
        __index_by_colldef(s_db, coll_defs)

################################################################################
            
def __index_by_colldef(ds_id, coll_defs):
    mongo_client = MongoClient(host=DB_MONGOHOST)
    i_db = mongo_client[ds_id]
    coll_names = i_db.list_collection_names()

    for collname, io_params in coll_defs.items():
        if collname not in coll_names:
            continue

        i_coll = i_db[ collname ]
        for p_k, p_v in io_params.items():
            special = p_v.get("type", "___none___")
            k = p_v["db_key"]
            if "2dsphere" in special:
                print(f'Creating GEOSPHERE index "{k}" in {collname} from {ds_id}')
                i_coll.create_index([(k, GEOSPHERE)])
                pass
            elif "compound" in special:
                print(f'Creating compound index "{k}" in {collname} from {ds_id}')
                i_coll.create_index(k)
                pass
            else:
                print(f'Creating index "{k}" in {collname} from {ds_id}')
                try:
                    m = i_coll.create_index(k)
                    print(m)
                except Exception:
                    print(f'¡¡¡ Index "{k}" in {collname} from {ds_id} has one with same id !!!')

