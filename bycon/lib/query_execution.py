from uuid import uuid4
from pymongo import MongoClient

from config import *
from bycon_helpers import *
from schema_parsing import RecordsHierarchy

################################################################################

class ByconDatasetResults():
    def __init__(self, ds_id, BQ):
        self.dataset_results = {}
        self.dataset_id = ds_id
        self.entity_defaults = BYC["entity_defaults"]
        self.res_ent_id = r_e_id = str(BYC.get("response_entity_id", "___none___"))
        self.data_db = MongoClient(host=DB_MONGOHOST)[ds_id]

        # This is bycon and model specific; in the default model there would also
        # be `run` (which has it's data here as part of `analysis`). Also in
        # `bycon` we have `phenopacket` which is a derived entity.
        # TODO: limit to the lowest level & upstream?
        # q_e_d = self.entity_defaults.get(self.res_ent_id, {})
        # self.queried_entities = q_e_d.get("upstream", [])

        self.queried_entities = RecordsHierarchy().entities()
        self.res_obj_defs = {}
        self.queries = {}
        for e in self.queried_entities:
            e_d = self.entity_defaults.get(e, {})
            c = e_d.get("collection", "___none___")
            self.res_obj_defs.update({f'{c}.id': {
                "collection": c,
                "entity_id": e,
                "id_parameter": f'{e}_id',
                "upstream_ids": [f'{x}_id' for x in RecordsHierarchy().upstream(e)]
            }})

        self.id_responses = {}

        self.__generate_queries(BQ)
        self.__run_stacked_queries()
        self.__requery_to_aggregate()
        self.__set_dataset_results()


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def retrieveResults(self):
        return self.dataset_results


    # -------------------------------------------------------------------------#

    def retrieve_individual_ids(self):
        return self.dataset_results.get("individuals.id", {}).get("target_values", [])


    # -------------------------------------------------------------------------#

    def retrieve_biosample_ids(self):
        return self.dataset_results.get("biosamples.id", {}).get("target_values", [])


    # -------------------------------------------------------------------------#

    def retrieve_analysis_ids(self):
        return self.dataset_results.get("analyses.id", {}).get("target_values", [])


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __generate_queries(self, BQ):
        c_n_s = self.data_db.list_collection_names()
        q_e_s = BQ.get("entities", {})
        for e, q_o in q_e_s.items():
            c = q_o.get("collection", "___none___")
            if (q := q_o.get("query")) and c in c_n_s:
                self.queries.update({c: q})


    # -------------------------------------------------------------------------#

    def __run_stacked_queries(self):
        """
        The `self.queries` object

        """
        if not (q_e_s := self.queries.keys()):
            return

        for e in q_e_s:
            query = self.queries.get(e)
            ent_resp_def = self.res_obj_defs.get(f'{e}.id')
            self.__prefetch_entity_multi_id_response(ent_resp_def, query)


    # -------------------------------------------------------------------------#

    def __prefetch_entity_multi_id_response(self, h_o_def, query):
        """



        """
        t_c = h_o_def.get("collection")
        d_k_s = h_o_def.get("upstream_ids", [])
        m_k = h_o_def.get("id_parameter", "id")

        d_group = {'_id': 0, "distincts_id": {'$addToSet': f'$id'}}
        for d_k in d_k_s:
            dist_k = f'distincts_{d_k}'
            d_group.update({dist_k: {'$addToSet': f'${d_k}'}})

        if type(query) is not list:
            query = [query]

        for qq in query:
            # Aggregation pipeline to get distinct values for each key since
            # geo $near queries don't work in aggregation pipelines
            if "geo_location.geometry" in qq:
                ids = self.data_db[t_c].distinct("id", qq)
                qq = {"id": {"$in": ids}}

            pipeline = [
                { '$match': qq },
                { "$sample": { "size": 220000 }},
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
                    self.id_responses.update({id_k: {"values": list(set(ex_resp.get("values", [])) & set(id_matches[id_k]))}})
                else:
                    self.id_responses.update({id_k: {"values": id_matches[id_k]}})
                self.id_responses[id_k].update({"count": len(self.id_responses[id_k]["values"])})


    # -------------------------------------------------------------------------#

    def __refetch_entity_id_response(self, h_o_def, query):
        t_c = h_o_def.get("collection")
        id_k = h_o_def.get("id_parameter")
        ids = self.data_db[t_c].distinct("id", query)

        if (ex_resp := self.id_responses.get(id_k)):
            self.id_responses.update({id_k: {"values": list(set(ex_resp.get("values", [])) & set(ids))}})
        else:
            self.id_responses.update({id_k: {"values": ids}})
        self.id_responses[id_k].update({"count": len(self.id_responses[id_k]["values"])})


    # -------------------------------------------------------------------------#

    def __requery_to_aggregate(self):
        # requerying top-down to intersect for entities w/o shared keys - e.g. if
        # a variant query was run the variant_id values are not filtered by the
        # analysis ... queries since analyses don't know about variant_id values
        # TODO: rethink... this is a bit hardcoded/verbose
        # it would also be more efficient to stop processing at the lowest queried
        # entity and use this for all lover level handovers instead of
        # pre-generating them

        query = {"individual_id": {"$in": self.id_responses.get("individual_id").get("values", [])}}
        ent_resp_def = self.res_obj_defs.get(f'biosamples.id')
        self.__refetch_entity_id_response(ent_resp_def, query)

        query = {"biosample_id": {"$in": self.id_responses.get("biosample_id").get("values", [])}}
        ent_resp_def = self.res_obj_defs.get(f'analyses.id')
        self.__refetch_entity_id_response(ent_resp_def, query)

        # another special case - variants are only queried if previously queried
        # otherwise one creates a variant storage for potentially millions
        # of variants just matching biosamples ... etc.
        if self.id_responses.get("genomicVariant_id"):
            query = {"analysis_id": {"$in": self.id_responses.get("analysis_id").get("values", [])}}
            ent_resp_def = self.res_obj_defs.get(f'variants.id')
            self.__refetch_entity_id_response(ent_resp_def, query)

        elif "genomicVariant" in self.res_ent_id:
            # TODO: Has to be optimized for large numbers...
            e = "genomicVariant"
            id_p = f"{e}_id"
            v_ids = []
            for ana_id in self.id_responses.get("analysis_id").get("values", []):
                v_ids += self.data_db["variants"].distinct("id", {"analysis_id": ana_id})
            v_ids = list(set(v_ids))

            v_no = len(v_ids)
            if v_no > VARIANTS_RESPONSE_LIMIT:
                v_ids = return_paginated_list(v_ids, 0, VARIANTS_RESPONSE_LIMIT)
                BYC["WARNINGS"].append(f"Too many {e} values ({v_no}) for dataset {self.dataset_id}. Only the first {VARIANTS_RESPONSE_LIMIT} will be returned.")

            self.id_responses.update({id_p: {"values": v_ids, "count": v_no}})
            e_d = self.entity_defaults.get(e, {})
            c = e_d.get("collection", "___none___")
            self.res_obj_defs.update({f'{c}.id': {
                "collection": c,
                "entity_id": e,
                "id_parameter": id_p,
                "upstream_ids": [f'{x}_id' for x in RecordsHierarchy().upstream(e)]
            }})



    # -------------------------------------------------------------------------#

    def __set_dataset_results(self):
        for h_o_k, h_o_def in self.res_obj_defs.items():
            m_k = h_o_def.get("id_parameter", "id")
            e_r = {**h_o_def}
            if not (t_v_s := self.id_responses.get(m_k)):
                continue

            e_r.update({
                "id": str(uuid4()),
                "ds_id": self.dataset_id,
                "target_values": t_v_s.get("values", []),
                "target_count": t_v_s.get("count", 0),
                "original_queries": self.queries
            })

            self.dataset_results.update({h_o_k: e_r})


################################################################################
################################################################################
################################################################################
