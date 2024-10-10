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

        self.__generate_queries(BQ)
        

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def retrieveResults(self):
        self.__run_stacked_queries()
        return self.dataset_results


    # -------------------------------------------------------------------------#
    # ----------------------------- private ------------------------------------#
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
            if "variants" in e:
                continue
            query = self.queries.get(e)
            ent_resp_def = self.res_obj_defs.get(f'{e}.id')
            self.__prefetch_entity_response(ent_resp_def, query)

        analysis_q_l = []
        if (pre := self.dataset_results.get("analyses.id")):
            analysis_q_l.append({"id": {"$in":pre.get("target_values")}})
        if (pre := self.dataset_results.get("biosamples.id")):
            analysis_q_l.append({"biosample_id": {"$in":pre.get("target_values")}})
        if (pre := self.dataset_results.get("individuals.id")):
            analysis_q_l.append({"individual_id": {"$in":pre.get("target_values")}})

        if len(analysis_q_l) > 0:
            query = mongo_and_or_query_from_list(analysis_q_l)
            # CAVE: This would remove biosamples & individuals from the response
            #       if they don't have any associated analysis...
            ent_resp_def = self.res_obj_defs.get("analyses.id")
            self.__prefetch_entity_response(ent_resp_def, query)
            ent_resp_def = self.res_obj_defs.get("analyses.biosample_id->biosamples.id")
            self.__prefetch_entity_response(ent_resp_def, query)
            ent_resp_def = self.res_obj_defs.get("analyses.individual_id->individuals.id")
            self.__prefetch_entity_response(ent_resp_def, query)

        self.__run_variants_query()
        self.__run_multi_variants_query()

        # prdbug(self.dataset_results)


    # -------------------------------------------------------------------------#

    def __run_variants_query(self):
        if not self.queries.get("variants"):
            return
        v_q_l = self.queries["variants"].copy()
        if type(v_q_l) is not list:
            v_q_l = [v_q_l]

        query = v_q_l.pop(0)
        if (pre := self.dataset_results.get("analyses.id")):
            query = {"$and":[
                {"analysis_id": {"$in":pre.get("target_values")}},
                query
            ]}
        self.__update_dataset_results_from_variants(query)


    # -------------------------------------------------------------------------#

    def __run_multi_variants_query(self):
        # first query has to be popped of by
        # also, biosamples.id exists already in results
        # TODO: make aggregation entity flexible, depending on requested schema
        if not self.queries.get("variants"):
            return
        variants_query = self.queries["variants"]
        if type(variants_query) is not list:
            variants_query = [variants_query]
        # keeping the original
        queries = variants_query.copy()
        queries.pop(0)
        if len(queries) < 1:
            return

        prdbug(f' ====== {BYC["response_entity"]} =====')
        res_e_id = BYC.get("response_entity_id", "biosample")
        res_e_coll = BYC["response_entity"].get("collection", "biosamples")
        id_k = f'{res_e_id}_id'
        pref_k = f'variants.{id_k}->{res_e_coll}.id'
        agg_k = f'{res_e_coll}.id'

        if "variant" in (res_e_id).lower():
            id_k = 'biosample_id'
            pref_k = f'variants.{id_k}->biosamples.id'
            agg_k = 'biosamples.id'

        for v_q in queries:
            v_bsids = self.dataset_results[agg_k]["target_values"]
            prdbug(f'before {self.dataset_results[agg_k]["target_count"]}')
            if (len(v_bsids) == 0):
                break
            query = {"$and": [v_q, {id_k: {"$in": v_bsids}}]}
            # prdbug(query)
            ent_resp_def = self.res_obj_defs.get(pref_k)
            self.__prefetch_entity_response(ent_resp_def, query)
            prdbug(f'after {self.dataset_results[agg_k]["target_count"]}')

        v_bsids = self.dataset_results[agg_k]["target_values"]

        if len(variants_query) > 1:
            query = {"$or": variants_query}
        else:
            query = variants_query[0]
        if len(v_bsids) > 0:
            query = {"$and": [query, {id_k: {"$in": v_bsids}}]}
        else:
            # fallback for 0 match results
            query = {"$and": [query, {id_k: {"$in": ["___undefined___"]}}]}

        self.__update_dataset_results_from_variants(query)


    # -------------------------------------------------------------------------#

    def __update_dataset_results_from_variants(self, query):
        ent_resp_def = self.res_obj_defs.get("variants.id")
        self.__prefetch_entity_response(ent_resp_def, query)
        ent_resp_def = self.res_obj_defs.get("variants.analysis_id->analyses.id")
        self.__prefetch_entity_response(ent_resp_def, query)
        ent_resp_def = self.res_obj_defs.get("variants.biosample_id->biosamples.id")
        self.__prefetch_entity_response(ent_resp_def, query)
        ent_resp_def = self.res_obj_defs.get("variants.individual_id->individuals.id")
        self.__prefetch_entity_response(ent_resp_def, query)


    # -------------------------------------------------------------------------#

    def __prefetch_entity_response(self, h_o_def, query):
        s_c = h_o_def.get("source_collection")
        s_k = h_o_def.get("source_key")
        t_c = h_o_def.get("target_collection")
        t_k = h_o_def.get("target_key")

        dist = self.data_db[s_c].distinct(s_k, query)
        t_v_s = dist if dist else []

        e_r = {**h_o_def}
        e_r.update({
            "id": str(uuid4()),
            "source_db": self.dataset_id,
            "target_values": t_v_s,
            "target_count": len(t_v_s),
            "original_queries": self.queries
        })

        r_k = f'{t_c}.{t_k}'
        self.dataset_results.update({r_k: e_r})
        return


################################################################################
################################################################################
################################################################################
