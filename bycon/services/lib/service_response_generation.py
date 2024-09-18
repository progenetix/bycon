from deepmerge import always_merger
from os import environ

from beacon_response_generation import BeaconResponseMeta
from bycon_helpers import mongo_result_list, mongo_test_mode_query, return_paginated_list
from cgi_parsing import prdbug
from config import AUTHORIZATIONS, BYC, BYC_PARS
from export_file_generation import *
from response_remapping import *
from schema_parsing import object_instance_from_schema_name

from service_helpers import set_selected_delivery_keys

################################################################################

class ByconautServiceResponse:

    def __init__(self, response_schema="byconautServiceResponse"):
        self.response_schema = response_schema
        self.requested_granularity = BYC_PARS.get("requested_granularity", "record")
        # TBD for authentication? 
        self.returned_granularity = BYC.get("returned_granularity", "record")
        self.beacon_schema = BYC["response_entity"].get("beacon_schema", "___none___")
        self.data_response = object_instance_from_schema_name(response_schema, "")
        self.error_response = object_instance_from_schema_name("beaconErrorResponse", "")
        self.data_response.update({"meta": BeaconResponseMeta(self.data_response).populatedMeta() })

        return
    

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def collationsResponse(self):
        if not "byconautServiceResponse" in self.response_schema:
            return

        colls = ByconCollations().populatedCollations()
        self.data_response["response"].update({"results": colls})
        self.__service_response_update_summaries()
        self.__serviceResponse_force_granularities()
        return self.data_response


    # -------------------------------------------------------------------------#

    def emptyResponse(self):
        if not "byconautServiceResponse" in self.response_schema:
            return
        return self.data_response


    # -------------------------------------------------------------------------#

    def populatedResponse(self, results=[]):
        if not "byconautServiceResponse" in self.response_schema:
            return
        self.data_response["response"].update({"results": results})
        self.__service_response_update_summaries()
        self.__serviceResponse_force_granularities()
        return self.data_response


    # -------------------------------------------------------------------------#

    def errorResponse(self):
        return self.error_response


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

        return

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

class ByconCollations:
    def __init__(self):
        self.delivery_method = BYC_PARS.get("method", "___none___")
        self.output = BYC_PARS.get("output", "___none___")
        self.response_entity_id = BYC.get("response_entity_id", "filteringTerm")
        self.path_id_value = BYC.get("request_entity_path_id_value", False)
        self.filter_collation_types = set()
        self.collations = []

        return

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
        d_k = set_selected_delivery_keys(s_c.get("method_keys", []))

        c_id = BYC_PARS.get("id", "")
        # TODO: This should be derived from some entity definitions
        # TODO: whole query generation in separate function ...
        query = {}

        prdbug(BYC.get("BYC_FILTERS", []))

        if BYC["TEST_MODE"] is True:
            t_m_c = BYC_PARS.get("test_mode_count", 5)
            query = mongo_test_mode_query(BYC["BYC_DATASET_IDS"][0], f_coll, t_m_c)
        elif len(c_id) > 0:
            query = { "id": c_id }
        else:
            q_list = []
            ft_fs = []
            for f in BYC.get("BYC_FILTERS", []):
                ft_fs.append('(' + f.get("id", "___none___") + ')')
            if len(ft_fs) > 0:
                f_s = '|'.join(ft_fs)
                f_re = re.compile(r'^' + '|'.join(ft_fs))
            else:
                f_re = None
            if f_re is not None:
                q_list.append({"id": { "$regex": f_re}})
            q_types = BYC_PARS.get("collation_types", [])
            if len(q_types) > 0:
                q_list.append({"collation_type": {"$in": q_types }})

            if len(q_list) == 1:
                query = q_list[0]
            elif len(q_list) > 1:
                query = {"$and": q_list}

        prdbug(f'Collation query: {query}')
        
        # TODO
        # if not query:
        #     warning = 'No limit (filters, collationTypes, id) on collation listing -> abortin...'

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

