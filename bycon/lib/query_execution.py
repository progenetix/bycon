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

        self.__generate_queries(BQ)
        self.__run_stacked_queries()
        self.__requery_to_aggregate()
        self.__set_dataset_results()


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def retrieveResults(self):
        prdbug(self.dataset_results)
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
        # prdbug(self.queries)


    # -------------------------------------------------------------------------#

    def __run_stacked_queries(self):
        if not (q_e_s := self.queries.keys()):
            return

        for e in q_e_s:
            query = self.queries.get(e)
            ent_resp_def = self.res_obj_defs.get(f'{e}.id')
            self.__prefetch_entity_multi_id_response(ent_resp_def, query)


    # -------------------------------------------------------------------------#

    def __prefetch_entity_multi_id_response(self, h_o_def, query):
        t_c = h_o_def.get("collection")
        d_k_s = h_o_def.get("upstream_ids", [])
        m_k = h_o_def.get("mapped_id", "id")

        d_group = {'_id': 0, "distincts_id": {'$addToSet': f'$id'}} 
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
            result = list(self.data_db[t_c].aggregate(pipeline))

            id_matches = {m_k: []}
            for d_k in d_k_s:
                id_matches.update({d_k: []})

            if result:
                id_matches.update({m_k: result[0].get("distincts_id", [])})
                for d_k in d_k_s:
                    dist_k = f'distincts_{d_k}'
                    id_matches.update({d_k: result[0].get(dist_k, [])})

            for id_k in id_matches:
                if (ex_resp := self.id_responses.get(id_k)):
                    self.id_responses.update({id_k: list(set(ex_resp) & set(id_matches[id_k]))})
                else:
                    self.id_responses.update({id_k: id_matches[id_k]})


    # -------------------------------------------------------------------------#

    def __requery_to_aggregate(self):
        # requerying top-down to intersect for entities w/o shared keys - e.g. if
        # a variant query was run the variant_id values are not filtered by the
        # analysis ... queries since analyses don't know about variant_id values
        if (ind_ids := self.id_responses.get("individual_id")):
            query = [{"individual_id": {"$in": ind_ids}}]
            ent_resp_def = self.res_obj_defs.get(f'biosamples.id')
            self.__prefetch_entity_multi_id_response(ent_resp_def, query)

        if (bios_ids := self.id_responses.get("biosample_id")):
            query = [{"biosample_id": {"$in": bios_ids}}]
            ent_resp_def = self.res_obj_defs.get(f'analyses.id')
            self.__prefetch_entity_multi_id_response(ent_resp_def, query)

        if (ana_ids := self.id_responses.get("analysis_id")):
            if self.id_responses.get("variant_id"):
                query = [{"analysis_id": {"$in": ana_ids}}]
                ent_resp_def = self.res_obj_defs.get(f'variants.id')
                self.__prefetch_entity_multi_id_response(ent_resp_def, query)


    # -------------------------------------------------------------------------#

    def __set_dataset_results(self):
        for h_o_k, h_o_def in self.res_obj_defs.items():
            m_k = m_k = h_o_def.get("mapped_id", "id")
            e_r = {**h_o_def}
            if not (t_v_s := self.id_responses.get(m_k)):
                continue
            e_r.update({
                "id": str(uuid4()),
                "ds_id": self.dataset_id,
                "target_values": t_v_s,
                "target_count": len(t_v_s),
                "original_queries": self.queries
            })
            # prdbug(e_r)
            self.dataset_results.update({h_o_k: e_r})


################################################################################
################################################################################
################################################################################
