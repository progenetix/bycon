import json, sys
from datetime import datetime
from deepmerge import always_merger
from os import environ

from config import *

from bycon_helpers import *
from handover_generation import dataset_response_add_handovers
from query_execution import ByconDatasetResults # execute_bycon_queries
from query_generation import ByconQuery
from read_specs import load_yaml_empty_fallback
from response_remapping import *
from variant_mapping import ByconVariant
from schema_parsing import get_schema_file_path, object_instance_from_schema_name
from service_utils import set_special_modes

################################################################################


class BeaconResponseMeta:
    def __init__(self, data_response=None):
        self.beacon_schema = BYC["response_entity"].get("beacon_schema", "___none___")
        self.response_meta = object_instance_from_schema_name("beaconResponseMeta", "")
        self.data_response = data_response
        self.record_queries = None


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def populatedMeta(self, record_queries=None):
        if self.data_response:
            self.response_meta = always_merger.merge(self.response_meta, self.data_response.get("meta", {}))

        self.__meta_add_parameters()
        self.__meta_add_received_request_summary_parameters()
        return self.response_meta


    # -------------------------------------------------------------------------#
    # ----------------------------- private ------------------------------------#
    # -------------------------------------------------------------------------#

    def __meta_add_parameters(self):
        r_m = self.response_meta
        if BYC["TEST_MODE"] is True:
            r_m.update({"test_mode": BYC["TEST_MODE"]})
        r_m.update({"returned_granularity": BYC["returned_granularity"]})

        info = BYC["entity_defaults"]["info"].get("content", {"api_version": "___none___"})
        for p in ["api_version", "beacon_id"]:
            if p in info.keys():
                r_m.update({p: info.get(p, "___none___")})

        # TODO: If keeping this - update after query etc.
        if len(BYC["WARNINGS"]) > 0:
            r_m.update({"warnings": BYC["WARNINGS"]})
        for p in ("info"):
            if not (p_v := r_m.get(p)):
                r_m.pop(p, None)

        self.response_meta.update(r_m)


    # -------------------------------------------------------------------------#

    def __meta_add_received_request_summary_parameters(self):
        r_m = self.response_meta
        if self.record_queries:
            r_m.update({"info": always_merger.merge(r_m.get("info", {}), {"original_queries": self.record_queries})})
        if "returned_schemas" in r_m:
            r_m.update({"returned_schemas":[self.beacon_schema]})

        if not "received_request_summary" in r_m:
            return

        r_r_s = r_m["received_request_summary"]
        r_r_s.update({
            "requested_schemas": [self.beacon_schema]
        })
        if BYC["TEST_MODE"] is True:
            r_r_s.update({"test_mode": BYC["TEST_MODE"]})

        r_r_s.update({"pagination": {"skip": BYC_PARS.get("skip"), "limit": BYC_PARS.get("limit")}})
        r_r_s.update({"dataset_ids": BYC["BYC_DATASET_IDS"]})

        vargs = BYC_VARGS
        # TODO: a bit hacky; len == 1 would be the default assemblyId ...
        if len(BYC_VARGS.keys()) > 0:
            r_r_s.update({"request_parameters":{"g_variant":BYC_VARGS}})

        fs = BYC["BYC_FILTERS"]
        fs_p = []
        if len(fs) > 0:
            for f in fs:
                fs_p.append(f.get("id"))
        r_r_s.update({"filters":fs_p})

        for p in ["include_resultset_responses", "requested_granularity"]:
            if p in BYC_PARS and p in r_r_s:
                r_r_s.update({p: BYC_PARS.get(p)})

        for q in ["cohort_ids", "cyto_bands", "chro_bases"]:
            if q in BYC_PARS:
                r_r_s.update({"request_parameters": always_merger.merge( r_r_s.get("request_parameters", {}), { "cohort_ids": BYC_PARS.get(q) })})

        info = BYC["entity_defaults"]["info"].get("content", {"api_version": "___none___"})
        for p in ["api_version", "beacon_id"]:
            r_r_s.update({p: info.get(p, "___none___")})

        self.response_meta.update({"received_request_summary": r_r_s})

        return


################################################################################

class BeaconErrorResponse:
    """
    This response class is used for all the info / map / configuration responses
    which have the same type of `meta`.
    The responses are then provided by the dedicated methods
    """
    def __init__(self):
        self.error_response = object_instance_from_schema_name("beaconErrorResponse", "")
        self.meta = BeaconResponseMeta().populatedMeta()
        self.errors = BYC.get("ERRORS", [])

    
    # -------------------------------------------------------------------------#

    def error(self, error_code=422):
        self.error_response.update({
            "error": {"error_code": error_code, "error_message": ", ".join(self.errors)},
            "meta": self.meta
        })
        return self.error_response


    # -------------------------------------------------------------------------#

    def respond_if_errors(self, error_code=422):
        prdbug(len(self.errors))
        if len(self.errors) < 1:
            return False
        self.error_response.update({
            "error": {"error_code": error_code, "error_message": ", ".join(self.errors)},
            "meta": self.meta
        })
        print_json_response(self.error_response)


################################################################################

class BeaconInfoResponse:
    """
    This response class is used for all the info / map / configuration responses
    which have the same type of `meta`.
    The responses are then provided by the dedicated methods
    """
    def __init__(self):
        self.beacon_schema = BYC["response_entity"].get("beacon_schema", "___none___")
        self.response_entity_id = BYC.get("response_entity_id", "info")
        self.entity_defaults = BYC.get("entity_defaults", {})
        self.data_response = object_instance_from_schema_name("beaconInfoResponse", "")
        self.data_response.update({"meta": BeaconResponseMeta().populatedMeta() })
        self.info_response_content = {}

        return
    

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def populatedInfoResponse(self):
        self.__populateInfoResponse()
        response = self.info_response_content
        self.__response_add_returned_schemas()
        r_k_s = []
        for p in response.keys():
            if "NoneType" in str(type(response[p])):
                r_k_s.append(p)
        for p in r_k_s:
            response.pop(p, None)
        self.data_response.update({"response":response})
        return self.data_response


    # -------------------------------------------------------------------------#
    # ---------------------------- private ------------------------------------#
    # -------------------------------------------------------------------------#

    def __populateInfoResponse(self):
        if "configuration" in self.response_entity_id:
            c_f = get_schema_file_path("beaconConfiguration")
            self.info_response_content = load_yaml_empty_fallback(c_f)
            return
        if "beaconMap" in self.response_entity_id:
            c_f = get_schema_file_path("beaconMap")
            self.info_response_content = load_yaml_empty_fallback(c_f)
            return
        if "entryType" in self.response_entity_id:
            c_f = get_schema_file_path("beaconConfiguration")
            e_t_s = load_yaml_empty_fallback(c_f)
            self.info_response_content = {"entry_types": e_t_s["entryTypes"] }
            return
        if "info" in self.response_entity_id:
            info = self.entity_defaults.get("info", {})
            pgx_info = info.get("content", {})
            beacon_info = object_instance_from_schema_name("beaconInfoResults", "")
            for k in beacon_info.keys():
                if k in pgx_info:
                    beacon_info.update({k:pgx_info[k]})
            self.info_response_content = beacon_info
            return


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __response_add_returned_schemas(self):
        if not "info" in self.response_entity_id:
            return

        ets = set()
        beacon_schemas = []
        for e_t, e_d in self.entity_defaults.items():
            if e_d.get("is_beacon_default", False) is True and e_t not in ets:
                beacon_schemas.append(e_d.get("beacon_schema", {}))
                ets.add(e_t)

        self.data_response.update( { "returned_schemas": beacon_schemas } )


################################################################################

class BeaconDataResponse:
    def __init__(self):
        self.user_name = BYC.get("USER", "anonymous")
        self.include_handovers = BYC_PARS.get("include_handovers", False)
        self.response_entity_id = BYC.get("response_entity_id")
        self.beacon_schema = BYC["response_entity"].get("beacon_schema", "___none___")
        self.record_queries = {}
        self.response_schema = BYC.get("response_schema", "___none___")
        self.data_response = object_instance_from_schema_name(BYC["response_schema"], "")
        self.data_response.update({"meta": BeaconResponseMeta(self.data_response).populatedMeta() })
        for m in ["beacon_handovers", "info"]:
            self.data_response.pop(m, None)
        self.data_time_init = datetime.datetime.now()

        return
    

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def dataResponseFromEntry(self):
        rp_id = self.response_entity_id
        prdbug(self.response_schema)
        if "beaconResultsetsResponse" in self.response_schema:
            return self.resultsetResponse()
        if "beaconCollectionsResponse" in self.response_schema:
            return self.collectionsResponse()
        if "beaconFilteringTermsResponse" in self.response_schema:
            return self.filteringTermsResponse()

    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def resultsetResponse(self):
        dbm = f'... resultsetResponse start, schema {self.response_schema}'
        prdbug(dbm)
        if not "beaconResultsetsResponse" in self.response_schema:
            return

        self.result_sets_start = datetime.datetime.now()
        self.result_sets, self.record_queries = ByconResultSets().get_populated_result_sets()
        self.__acknowledge_HIT()
        self.__acknowledge_MISS()
        self.data_response["response"].update({"result_sets": self.result_sets})
        self.__resultset_response_update_summaries()
        self.__resultSetResponse_force_autorized_granularities()

        if not self.data_response.get("info"):
            self.data_response.pop("info", None)

        self.__response_clean_parameters()
        self.__check_switch_to_error_response()
        self.result_sets_end = datetime.datetime.now()
        self.result_sets_duration = self.result_sets_end - self.result_sets_start

        self.data_response.update({"meta": BeaconResponseMeta(self.data_response).populatedMeta(self.record_queries) })

        dbm = f'... data response duration was {self.result_sets_duration.total_seconds()} seconds'

        return self.data_response


    # -------------------------------------------------------------------------#

    def collectionsResponse(self):
        if not "beaconCollectionsResponse" in BYC["response_schema"]:
            return

        colls, queries = ByconCollections().populatedCollections()
        colls = self.__collections_response_remap_cohorts(colls)
        self.data_response["response"].update({"collections": colls})
        self.record_queries.update({"entities": queries})
        self.__collections_response_update_summaries()
        self.__check_switch_to_error_response()
        self.data_response.update({"meta": BeaconResponseMeta(self.data_response).populatedMeta(self.record_queries) })
        self.data_response.get("meta", {}).get("received_request_summary", {}).pop("include_resultset_responses", None)
        return self.data_response


    # -------------------------------------------------------------------------#

    def filteringTermsResponse(self):
        if not "beaconFilteringTermsResponse" in BYC["response_schema"]:
            return

        fts, ress, query = ByconFilteringTerms().populatedFilteringTerms()
        self.data_response["response"].update({"filtering_terms": fts})
        self.data_response["response"].update({"resources": ress})
        self.record_queries.update({"entities": {"filtering_terms": query}})
        self.__response_clean_parameters()
        self.__check_switch_to_error_response()
        self.data_response.update({"meta": BeaconResponseMeta(self.data_response).populatedMeta(self.record_queries) })
        return self.data_response


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __check_switch_to_error_response(self):
        r_q_e = self.record_queries.get("entities", {})
        if not r_q_e:
            BYC["ERRORS"].append("no valid query")
            self.data_response.update({"error": {"error_code": 422, "error_message": ", ".join(BYC["ERRORS"])}})
            self.data_response.pop("response", None)
            self.data_response.pop("response_summary", None)


    # -------------------------------------------------------------------------#

    def __resultSetResponse_force_autorized_granularities(self):
        a_g_s = BYC.get("authorized_granularities", {})
        prdbug(f'authorized_granularities: {a_g_s}')
        for rs in self.data_response["response"]["result_sets"]:
            rs_granularity = a_g_s.get(rs["id"], "boolean")
            if not "record" in rs_granularity:
                # TODO /CUSTOM: This non-standard modification removes the results
                # but keeps the resultSets structure (handovers ...)
                rs.pop("results", None)
            if "boolean" in rs_granularity:
                rs.pop("results_count", None)
        if "boolean" in BYC.get("returned_granularity", "boolean"):
            self.data_response["response_summary"].pop("num_total_results", None)
            self.data_response.pop("response", None)


    # -------------------------------------------------------------------------#

    def __acknowledge_HIT(self):
        if not "HIT" in (i_rs_r := BYC_PARS.get("include_resultset_responses", "ALL")).upper():
            return
        rss = [rs for rs in self.result_sets if rs.get("exists", True) is True]
        self.result_sets = rss


    # -------------------------------------------------------------------------#

    def __acknowledge_MISS(self):
        if not "MISS" in (i_rs_r := BYC_PARS.get("include_resultset_responses", "ALL")).upper():
            return
        rss = [rs for rs in self.result_sets if rs.get("exists", True) is False]
        self.result_sets = rss


    # -------------------------------------------------------------------------#

    def __collections_response_remap_cohorts(self, colls=[]):
        if not "cohort" in BYC.get("response_entity_id", "___none___"):
            return colls
        pop_keys = ["_id", "child_terms", "code_matches", "count", "dataset_id", "db_key", "namespace_prefix", "ft_type", "collation_type", "hierarchy_paths", "parent_terms", "scope"]
        for c in colls:
            c_k = f'{c.get("scope", "")}.{c.get("db_key", "")}'
            c.update({
                "id": c.get("id", "___none___"),
                "cohort_type": "beacon-defined",
                "cohort_size": c.get("count"),
                "name": c.get("label", ""),
                # "inclusion_criteria": {
                #     "description": c.get("description", "NA"),
                #     c_k: c.get("id"),
                #     "dataset_id": c.get("dataset_id")
                # }
            })
            for k in pop_keys:
                c.pop(k, None)

        return colls


    # -------------------------------------------------------------------------#

    def __response_clean_parameters(self):
        r_m = self.data_response.get("response", {})
        r_m.pop("$schema", None)


    # -------------------------------------------------------------------------#

    def __resultset_response_update_summaries(self):
        if not "beaconResultsetsResponse" in BYC["response_schema"]:
            return
        if not "response" in self.data_response:
            return
        rsr = self.data_response["response"].get("result_sets")
        if not rsr:
            return

        t_count = 0
        t_exists = False
        for i, r_s in enumerate(rsr):
            r_c = r_s.get("results_count", 0)
            t_count += r_c

        if t_count > 0:
            t_exists = True

        self.data_response.update({
            "response_summary": {
                "num_total_results": t_count,
                "exists": t_exists
            }
        })

        return


   # -------------------------------------------------------------------------#

    def __collections_response_update_summaries(self):
        if not "beaconCollectionsResponse" in BYC["response_schema"]:
            return
        if not "response" in self.data_response:
            return
        c_r = self.data_response["response"].get("collections")
        if not c_r:
            return

        t_count = len(c_r)

        if t_count > 0:
            t_exists = True

        self.data_response.update({
            "response_summary": {
                "num_total_results": t_count,
                "exists": t_exists
            }
        })

        return


################################################################################
################################################################################
################################################################################

class ByconFilteringTerms:
    def __init__(self):
        self.response_entity_id = BYC.get("response_entity_id", "filteringTerm")
        self.data_collection = BYC["response_entity"].get("collection", "collations")
        self.filter_collation_types = set()
        self.filtering_terms = []
        self.filter_resources = []
        self.filtering_terms_query = {}

        return

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def populatedFilteringTerms(self):
        self.__return_filtering_terms()
        self.__return_filter_resources()
        return self.filtering_terms, self.filter_resources, self.filtering_terms_query

    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __return_filtering_terms(self):

        f_coll = self.data_collection

        ft_fs = []
        for f in BYC["BYC_FILTERS"]:
            ft_fs.append('(' + f.get("id", "___none___") + ')')
        if len(ft_fs) > 0:
            f_s = '|'.join(ft_fs)
            f_re = re.compile(r'^' + '|'.join(ft_fs))
        else:
            f_re = None

        query = {}
        q_list = []

        mode = BYC_PARS.get("mode", "___none___")
        if len(q_types := BYC_PARS.get("collation_types", [])) > 0:
            q_list.append({"collation_type": {"$in": q_types }})
        elif not "withpubmed" in mode:
            query = {"collation_type": {"$not": {"$regex":"pubmed"}}}

        if len(q_list) == 1:
            query = q_list[0]
        elif len(q_list) > 1:
            query = {"$and": q_list}

        if BYC["TEST_MODE"] is True:
            query = mongo_test_mode_query(BYC["BYC_DATASET_IDS"][0], f_coll)

        for ds_id in BYC["BYC_DATASET_IDS"]:
            fields = {"_id": 0}
            f_s = mongo_result_list(ds_id, f_coll, query, fields)
            t_f_t_s = []
            for f in f_s:
                self.filter_collation_types.add(f.get("collation_type", None))
                f_t = {"count": f.get("count", 0)}
                for k in ["id", "label"]:
                    if k in f:
                        f_t.update({k: f[k]})
                f_t.update({"type": f.get("ft_type", "ontologyTerm")})
                if "ontologyTerm" in f_t["type"]:
                    f_t.update({"type": f.get("name", "ontologyTerm")})
                ft_k = f.get("db_key")
                ft_s = f.get("scope")
                if ft_k and ft_s:
                    f_t.update({"target": f'{ft_s}.{ft_k}'})

                lab = f_t.get("label")
                if lab is None:
                    f_t.pop("label", None)

                # TODO: this is not required & also not as defined (singular `scope`)
                t_f_t_s.append(f_t)
            self.filtering_terms.extend(t_f_t_s)

        self.filtering_terms_query = query

        return


    # -------------------------------------------------------------------------#

    def __return_filter_resources(self):
        r_o = {}
        f_d_s = BYC.get("filter_definitions", {})
        collation_types = list(self.filter_collation_types)
        res_schema = object_instance_from_schema_name("beaconFilteringTermsResults", "definitions/Resource",
                                                      "json")
        for c_t in collation_types:
            if c_t not in f_d_s:
                continue
            f_d = f_d_s[c_t]
            if not "ontologyTerm" in f_d.get("ft_type"):
                continue
            r = {}
            for k in res_schema.keys():
                if k in f_d:
                    r.update({k: f_d[k]})
            r_o.update({f_d["namespace_prefix"]: r})
        for k, v in r_o.items():
            self.filter_resources.append(v)

        return


################################################################################
################################################################################
################################################################################

class ByconCollections:

    def __init__(self):
        self.response_entity_id = BYC.get("response_entity_id", "dataset")
        self.data_collection = BYC["response_entity"].get("collection", "collations")
        self.collections = []
        self.collections_queries = {}
        return


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def populatedCollections(self):
        self.__collections_return_datasets()
        self.__collections_return_cohorts()
        return self.collections, self.collections_queries

    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __collections_return_datasets(self):
        if not "dataset" in self.response_entity_id:
            return
        dbstats = __datasets_update_latest_stats()
        self.collections = dbstats
        self.collections_queries.update({"datasets":{}})

        return


    # -------------------------------------------------------------------------#

    def __datasets_update_latest_stats():
        results = []
        stat = []

        stats = MongoClient(host=DB_MONGOHOST)[HOUSEKEEPING_DB][HOUSEKEEPING_INFO_COLL].find( { }, { "_id": 0 } ).sort( {"date": -1} ).limit( 1 )
        stats = list(stats)

        if len(stats) > 0:
            stat = stats[0]
        else:
            return results
        for coll_id, coll in BYC["dataset_definitions"].items():
            if not coll_id in BYC.get("BYC_DATASET_IDS", []):
                continue
            if "datasets" in stat:
                if (ds_vs := stat[ "datasets" ].get(coll_id)):
                    if "filtering_terms" in BYC["response_entity_id"]:
                        coll.update({ "filtering_terms": ds_vs.get("filtering_terms", []) } )
            # TODO: remove verifier hack
            for t in ["createDateTime", "updateDateTime"]:
                d = str(d_s.get(t, "1967-11-11"))
                if re.match(r'^\d\d\d\d\-\d\d\-\d\d$', d):
                    coll.update({t:f'{d}T00:00:00+00:00'})
            results.append(coll)
        return results


    # -------------------------------------------------------------------------#

    def __collections_return_cohorts(self):
        if not "cohort" in self.response_entity_id:
            return

        # TODO: reshape cohorts according to schema
        cohorts =  []
        query = { "collation_type": "pgxcohort" }
        limit = 0
        if BYC["TEST_MODE"] is True:
            limit = BYC_PARS.get("test_mode_count", 5)
        else:
            c_q = BYC_PARS.get("filters", [])
            # if len(c_q) < 1:
            #     if len(self.path_id_value) > 0:
            #         c_q = self.path_id_value

            if len(c_q) > 0:
                query = {
                    "$and": [
                        query,
                        { "id": {"$in": c_q} }
                    ]
                }

        mongo_client = MongoClient(host=DB_MONGOHOST)
        for ds_id in BYC["BYC_DATASET_IDS"]:
            mongo_db = mongo_client[ ds_id ]        
            mongo_coll = mongo_db[ "collations" ]
            for cohort in mongo_coll.find( query, limit=limit ):
                cohorts.append(cohort)

        self.collections = cohorts
        self.collections_queries.update({"cohorts":query})

        return


################################################################################

class ByconResultSets:
    def __init__(self):
        self.datasets_results = dict()  # the object with matched ids per dataset, per h_o
        self.datasets_data = dict()     # the object with data of requested entity per dataset
        self.result_sets = list()       # data rewrapped into the resultSets list
        self.flattened_data = list()    # data from all resultSets as flat list
        self.entity_defaults = BYC.get("entity_defaults", {})
        self.response_entity_id = BYC.get("response_entity_id", "biosample")
        self.limit = BYC_PARS.get("limit")
        self.skip = BYC_PARS.get("skip")

        self.record_queries = ByconQuery().recordsQuery()
        self.__create_empty_result_sets()
        self.__get_handover_access_key()
        self.__retrieve_datasets_results()


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def get_record_queries(self):
        return self.record_queries


    # -------------------------------------------------------------------------#
    def get_populated_result_sets(self):
        self.__retrieve_datasets_data()
        self.__retrieve_variants_data()
        self.__populate_result_sets()
        self.__result_sets_save_handovers()
        return self.result_sets, self.record_queries


    # -------------------------------------------------------------------------#

    def get_flattened_data(self):
        self.__retrieve_datasets_data()
        self.__retrieve_variants_data()

        for ds_id, data in self.datasets_data.items():
            for r in data:
                r.update({"dataset_id": ds_id})
                self.flattened_data.append(r)
        return self.flattened_data


    # -------------------------------------------------------------------------#

    def datasetsResults(self):
        return self.datasets_results


    # -------------------------------------------------------------------------#

    def dataset_results_individual_ids(self, ds_id="___none___"):
        individual_ids = set()
        self.response_entity_id = "individual"
        self.__retrieve_datasets_data()
        if not ds_id in self.datasets_data:
            BYC["ERRORS"].append("no correct dataset id provided to `dataset_results_biosample_ids`")
            return []

        data = self.datasets_data[ds_id]
        for s in data:
            if (ind_id := s.get("individual_id")):
                individual_ids.add(ind_id)

        return list(individual_ids)


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __get_handover_access_key(self):
        e_d_s = self.entity_defaults.get(self.response_entity_id, {})
        self.handover_key = e_d_s.get("h->o_access_key", "___none___")
        return


    # -------------------------------------------------------------------------#

    def __result_sets_save_handovers(self):
        ho_client = MongoClient(host=DB_MONGOHOST)
        ho_coll = ho_client[HOUSEKEEPING_DB][HOUSEKEEPING_HO_COLL]
        for ds_id, d_s in self.datasets_results.items():
            if not d_s:
                continue
            info = {"counts": {}}
            for h_o_k, h_o in d_s.items():
                if not "target_values" in h_o:
                    continue
                h_o_size = sys.getsizeof(h_o["target_values"])        
                dbm = f'Storage size for {ds_id}.{h_o_k}: {h_o_size / 1000}kb'
                prdbug(dbm)
                # TODO: warning/error for exclusion due to size (breaking the MongoDB storage...)
                if h_o_size < 15000000:
                    ho_coll.update_one( { "id": h_o["id"] }, { '$set': h_o }, upsert=True )
        ho_client.close()


    # -------------------------------------------------------------------------#

    def __create_empty_result_sets(self):
        r_set = object_instance_from_schema_name("beaconResultsets", "definitions/ResultsetInstance")
        r_sets = []
        for ds_id in BYC["BYC_DATASET_IDS"]:
            ds_rset = r_set.copy()
            ds_rset.update({
                "id": ds_id,
                "set_type": "dataset",
                "results_count": 0,
                "exists": False
                # "info": {"counts": {}}
            })
            r_sets.append(ds_rset)
        self.result_sets = r_sets
        return


    # -------------------------------------------------------------------------#

    def __retrieve_datasets_results(self):
        ds_r_start = datetime.datetime.now()
        for i, r_set in enumerate(self.result_sets):
            ds_id = r_set.get("id", "___none___")
            DR = ByconDatasetResults(ds_id, self.record_queries)
            ds_res = DR.retrieveResults()
            self.datasets_results.update({ds_id: ds_res})            
        ds_r_duration = datetime.datetime.now() - ds_r_start
        
        dbm = f'... datasets results querying needed {ds_r_duration.total_seconds()} seconds'
        prdbug(dbm)
        return


    # -------------------------------------------------------------------------#

    def __retrieve_datasets_data(self):
        if "variant" in self.response_entity_id.lower():
            return

        e_d_s = BYC["entity_defaults"].get(self.response_entity_id, {})

        ds_d_start = datetime.datetime.now()
        for ds_id, ds_results in self.datasets_results.items():
            if not ds_results:
                continue
            if (h_o_k := e_d_s.get("h->o_access_key", "___none___")) not in ds_results.keys():
                continue
            res = ds_results.get(h_o_k, {})
            q_k = res.get("target_key", "id")
            q_db = res.get("source_db", "___none___")
            q_coll = res.get("target_collection", "___none___")
            q_v_s = res.get("target_values", [])
            q_v_s = return_paginated_list(q_v_s, self.skip, self.limit)

            mongo_client = MongoClient(host=DB_MONGOHOST)
            data_coll = mongo_client[ q_db ][ q_coll ]

            r_s_res = []
            for q_v in q_v_s:
                o = data_coll.find_one({q_k: q_v })
                r_s_res.append(o)
            self.datasets_data.update({ds_id: r_s_res})

        ds_d_duration = datetime.datetime.now() - ds_d_start
        dbm = f'... datasets data retrieval needed {ds_d_duration.total_seconds()} seconds'
        prdbug(dbm)

        return


    # -------------------------------------------------------------------------#

    def __retrieve_variants_data(self):
        if not "variant" in self.response_entity_id.lower():
            return

        ds_v_start = datetime.datetime.now()
        for ds_id, ds_results in self.datasets_results.items():

            mongo_client = MongoClient(host=DB_MONGOHOST)
            data_db = mongo_client[ ds_id ]
            v_coll = mongo_client[ ds_id ][ "variants" ]

            r_s_res = []

            if "variants.id" in ds_results:
                q_v_s = ds_results["variants.id"]["target_values"]
                q_v_s = return_paginated_list(q_v_s, self.skip, self.limit)
                for v_id in q_v_s:
                    v = v_coll.find_one({"id":v_id})
                    r_s_res.append(v)
                self.datasets_data.update({ds_id: r_s_res})

        ds_v_duration = datetime.datetime.now() - ds_v_start

        dbm = f'... variants retrieval needed {ds_v_duration.total_seconds()} seconds'
        prdbug(dbm)

        return


    # -------------------------------------------------------------------------#

    def __populate_result_sets(self):
        ds_v_start = datetime.datetime.now()
        for i, r_set in enumerate(self.result_sets):
            ds_id = r_set["id"]
            ds_res = self.datasets_results.get(ds_id)
            if not ds_res:
                continue
            r_set.update({"results_handovers": dataset_response_add_handovers(ds_id, self.datasets_results)})
            q_c = ds_res.get("target_count", 0)
            r_s_res = self.datasets_data.get(ds_id, [])
            r_s_res = list(x for x in r_s_res if x)
            r_s_res = reshape_resultset_results(ds_id, r_s_res)
            info = {"counts": {}}
            rs_c = len(r_s_res) if type(r_s_res) is list else 0
            for h_o_k, h_o in ds_res.items():
                if not "target_count" in h_o:
                    continue
                collection = h_o_k.split('.')[0]
                info["counts"].update({collection: h_o["target_count"]})
                entity = h_o.get("target_entity", "___none___")
                if entity == self.response_entity_id:
                    rs_c = h_o["target_count"]
            self.result_sets[i].update({
                "info": info,
                "response_entity_id" : self.response_entity_id,
                "results_count": rs_c,
                "exists": True if rs_c > 0 else False,
                "results": r_s_res
            })
        ds_v_duration = datetime.datetime.now() - ds_v_start
        dbm = f'... __populate_result_sets needed {ds_v_duration.total_seconds()} seconds'
        prdbug(dbm)
        return


################################################################################
# common response functions ####################################################
################################################################################

def print_json_response(this={}, status_code=200):
    if not "local" in ENV:
        print('Content-Type: application/json')
        print(f'status:{status_code}\n\n')

    # There are some "do not camelize" exceptions downstream
    prjsoncam(this) 
    print()
    exit()


################################################################################

def print_text_response(this="", status_code=200):
    if "server" in ENV:
        print('Content-Type: text/plain')
        print(f'status:{status_code}\n\n')

    print(this)
    print()
    exit()


################################################################################

def print_html_response(this="", status_code=200):
    if "server" in ENV:
        print('Content-Type: text/html')
        print('status:' + str(status_code))
        print()

    print(this)
    print()
    exit()


################################################################################

def print_uri_rewrite_response(uri_base="", uri_stuff=""):
    print("Status: 302")
    print("Location: {}{}".format(uri_base, uri_stuff))
    print()
    exit()

