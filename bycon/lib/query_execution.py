import random

from uuid import uuid4
from pymongo import MongoClient
from os import environ

from config import *
from bycon_helpers import mongo_and_or_query_from_list, prdbug, prjsonnice, test_truthy

################################################################################

class ByconDatasetResults():
    def __init__(self, ds_id, BQ):
        self.dataset_results = {}
        self.dataset_id = ds_id
        self.res_obj_defs = BYC["handover_definitions"]["h->o_methods"]
        self.res_ent_id = r_e_id = str(BYC.get("response_entity_id", "___none___"))
        self.data_db = MongoClient(host=environ.get("BYCON_MONGO_HOST", "localhost"))[ds_id]

        self.id_responses = {}
        # "variant_id": None,
        # "analysis_id": None,
        # "biosample_id": None,
        # "individual_id": None

        self.__generate_queries(BQ)
        prdbug(self.queries)
        self.__run_stacked_queries()
        for k in self.id_responses:
            prdbug(f'> finally > {k}: {len(self.id_responses.get(k, []))}')
        

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def retrieveResults(self):
        return self.dataset_results


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __generate_queries(self, BQ):
        c_n_s = self.data_db.list_collection_names()
        q_e_s = BQ.get("entities", {})
        self.queries = {}
        for q_e, q_o in q_e_s.items():
            c_n = q_o.get("collection", "___none___")
            if (q := q_o.get("query")) and c_n in c_n_s:
                self.queries.update({c_n: q})


    # -------------------------------------------------------------------------#

    def __run_stacked_queries(self):
        if not (q_e_s := self.queries.keys()):
            return

        for e in q_e_s:
            query = self.queries.get(e)
            ent_resp_def = self.res_obj_defs.get(f'{e}.id')
            self.__prefetch_entity_multi_id_response(ent_resp_def, query)

        # requerying top-down to intersect for entities w/o shared keys - e.g. if
        # a variant query was run the variant_id values are not filtered by the
        # analysis ... queries since analyses don't know about variant_id values

        if "individual_id" in self.id_responses:
            query = [{"id": {"$in": list(self.id_responses.get("individual_id"))}}]
            ent_resp_def = self.res_obj_defs.get(f'individuals.id')
            self.__prefetch_entity_multi_id_response(ent_resp_def, query)

            query = [{"individual_id": {"$in": list(self.id_responses.get("individual_id"))}}]
            ent_resp_def = self.res_obj_defs.get(f'biosamples.id')
            self.__prefetch_entity_multi_id_response(ent_resp_def, query)

        if "biosample_id" in self.id_responses:
            query = [{"biosample_id": {"$in": list(self.id_responses.get("biosample_id"))}}]
            ent_resp_def = self.res_obj_defs.get(f'analyses.id')
            self.__prefetch_entity_multi_id_response(ent_resp_def, query)

        if "analysis_id" in self.id_responses and "variant_id" in self.id_responses:
            query = [{"analysis_id": {"$in": list(self.id_responses.get("analysis_id"))}}]
            ent_resp_def = self.res_obj_defs.get(f'variants.id')
            self.__prefetch_entity_multi_id_response(ent_resp_def, query)

        prdbug(self.dataset_results.keys())


    # -------------------------------------------------------------------------#

    def __prefetch_entity_multi_id_response(self, h_o_def, query):
        s_c = h_o_def.get("source_collection")
        s_k = h_o_def.get("source_key")
        t_c = h_o_def.get("target_collection")
        t_k = h_o_def.get("target_key")
        d_k_s = h_o_def.get("distinct_keys", ["id"])
        m_k = h_o_def.get("mapped_key", "id")

        d_group = {'_id': 0}
        for d_k in d_k_s:
            dist_k = f'distincts_{d_k}'
            d_group.update({dist_k: {'$addToSet': f'${d_k}'}})

        if type(query) is not list:
            query = [query]

        for qq in query:

            # Aggregation pipeline to get distinct values for each key
            pipeline = [ 
                { '$match': qq },
                { '$group': d_group } 
            ]
            result = list(self.data_db[s_c].aggregate(pipeline))

            id_matches = {}
            for d_k in d_k_s:
                if d_k == 'id':
                    id_matches.update({m_k: []})
                else:
                    id_matches.update({d_k: []})

            if result:
                for d_k in d_k_s:
                    dist_k = f'distincts_{d_k}'
                    # print(f'>>>>> {dist_k}: {len(result[0].get(dist_k, []))}')
                    if d_k == 'id':
                        id_k = h_o_def.get("mapped_key", "id")
                        id_matches.update({id_k: result[0].get(dist_k, [])})
                    else:
                        id_matches.update({d_k: result[0].get(dist_k, [])})

            for id_k in id_matches:
                if (ex_resp := self.id_responses.get(id_k)):
                    self.id_responses.update({id_k: list(set(ex_resp) & set(id_matches[id_k]))})
                else:
                    self.id_responses.update({id_k: id_matches[id_k]})

        # this sets the match as an intersection with previous matches for the
        # same key
        t_v_s = self.id_responses.get(m_k, [])

        e_r = {**h_o_def}
        e_r.update({
            "id": str(uuid4()),
            "source_db": self.dataset_id,
            "target_values": t_v_s,    #t_v_s,
            "target_count": len(t_v_s),
            "original_queries": self.queries
        })

        r_k = f'{t_c}.{t_k}'
        self.dataset_results.update({r_k: e_r})


################################################################################
################################################################################
################################################################################
