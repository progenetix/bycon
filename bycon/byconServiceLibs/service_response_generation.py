from deepmerge import always_merger
from os import environ

from beacon_response_generation import BeaconResponseMeta, print_json_response
from bycon_helpers import mongo_result_list, mongo_test_mode_query, mongo_and_or_query_from_list, return_paginated_list
from parameter_parsing import prdbug
from config import AUTHORIZATIONS, BYC, BYC_PARS
from export_file_generation import *
from response_remapping import *
from schema_parsing import ByconSchemas

################################################################################

class ByconServiceResponse:

    def __init__(self, response_schema="byconServiceResponse"):
        self.response_schema = response_schema
        self.requested_granularity = BYC_PARS.get("requested_granularity", "record")
        # TBD for authentication? 
        self.returned_granularity = BYC.get("returned_granularity", "record")
        self.beacon_schema = BYC["response_entity"].get("beacon_schema", "___none___")
        self.data_response = ByconSchemas(self.response_schema, "").get_schema_instance()
        self.error_response = ByconSchemas("beaconErrorResponse", "").get_schema_instance()
        self.data_response.update({"meta": BeaconResponseMeta(self.data_response).populatedMeta() })
        if not self.data_response.get("info"):
            self.data_response.pop("info", None)

        return
    

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def collations_response(self):
        if not "byconServiceResponse" in self.response_schema:
            return

        colls = ByconCollations().populatedCollations()
        self.data_response["response"].update({"results": colls})
        self.__service_response_update_summaries()
        self.__serviceResponse_force_granularities()
        return self.data_response


    # -------------------------------------------------------------------------#

    def print_collations_response(self):
        self.collations_response()
        print_json_response(self.data_response)


    # -------------------------------------------------------------------------#

    def emptyResponse(self):
        if not "byconServiceResponse" in self.response_schema:
            return
        return self.data_response


    # -------------------------------------------------------------------------#

    def populated_response(self, results=[]):
        if not "byconServiceResponse" in self.response_schema:
            return
        self.data_response["response"].update({"results": results})
        self.__service_response_update_summaries()
        self.__serviceResponse_force_granularities()
        return self.data_response


    # -------------------------------------------------------------------------#

    def print_populated_response(self, results=[]):
        self.populated_response(results)
        print_json_response(self.data_response)


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __service_response_update_summaries(self):
        if not "response" in self.data_response:
            return
        c_r = self.data_response["response"].get("results", [])
        t_count = len(c_r)

        t_exists = True if t_count > 0 else False

        self.data_response.update({
            "response_summary": {
                "num_total_results": t_count,
                "exists": t_exists
            }
        })


    # -------------------------------------------------------------------------#

    def __serviceResponse_force_granularities(self):
        if not "record" in self.returned_granularity:
            self.data_response["response"].pop("results", None)
        if "boolean" in self.returned_granularity:
            self.data_response["response_summary"].pop("num_total_results", None)
            self.data_response.pop("response", None)


################################################################################
################################################################################
################################################################################

class CollationQuery:

    def __init__(self):
        self.collection = "collations"

        if BYC["TEST_MODE"] is True:
            self.query = mongo_test_mode_query(BYC["BYC_DATASET_IDS"][0], self.collection)
            return

        q_list = []
        all_ids = []
        filters = BYC_PARS.get("filters", [])
        c_types = BYC_PARS.get("collation_types", [])

        if len(filters) > 0:
            q_list.append({"id": {"$in": filters}})
        if len(c_types) > 0:
            q_list.append({"collation_type": {"$in": c_types }})
        self.query = mongo_and_or_query_from_list(q_list)

        # fallback to illicit query to avoid empty query / all ids
        if len(self.query.keys()) < 1:
            if "all" in c_types:
                self.query = {}
                return
            else:
                self.query = {"id":"___undefined___"}


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def getQuery(self):
        return self.query


################################################################################
################################################################################
################################################################################

class ByconCollations:
    def __init__(self):
        self.output = BYC_PARS.get("output", "___none___")
        self.response_entity_id = BYC.get("response_entity_id", "filteringTerm")
        self.filter_collation_types = set()
        self.collations = []


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def populatedCollations(self):
        self.__return_collations()
        return self.collations


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __return_collations(self):
        f_coll = "collations"
        s_c = BYC.get("service_config", {})
        d_k = BYC_PARS.get("delivery_keys", [])

        # TODO: This should be derived from some entity definitions
        query = CollationQuery().getQuery()

        prdbug(f'Collation query: {query}')
        
        s_s = { }
        for ds_id in BYC["BYC_DATASET_IDS"]:
            prdbug(f'... parsing collations for {ds_id}')

            fields = {"_id": 0}
            f_s = mongo_result_list(ds_id, f_coll, query, fields)
            for f in f_s:
                if BYC_PARS.get("include_descendant_terms", True) is False:
                    if int(f.get("code_matches", 0)) < 1:
                        continue
                i_d = f.get("id", "NA")
                if i_d not in s_s:
                    s_s[ i_d ] = { }
                if len(d_k) < 1:
                    d_k = list(f.keys())
                    d_k = [x for x in d_k if x not in ["_id", "frequencymap"]]
                for k in d_k:
                    if k in ["count", "code_matches", "cnv_analyses"]:
                        s_s[ i_d ].update({k: s_s[ i_d ].get(k, 0) + f.get(k, 0)})
                    elif k == "name":
                        s_s[ i_d ][ "type" ] = f.get(k)
                    else:
                        s_s[ i_d ][ k ] = f.get(k)
        
        for k, v in s_s.items():
            self.collations.append(v)

        return


################################################################################
################################################################################
################################################################################

