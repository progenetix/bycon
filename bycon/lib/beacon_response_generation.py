import json, requests, sys
from datetime import datetime
from deepmerge import always_merger
from os import environ, pardir, path
from random import sample as random_samples

from config import *

from bycon_helpers import *
from bycon_info import ByconInfo
from bycon_summarizer import ByconSummary
from handover_generation import dataset_response_add_handovers
from parameter_parsing import ByconFilters, ByconParameters
from query_execution import ByconDatasetResults # execute_bycon_queries
from query_generation import ByconQuery
from response_remapping import *
from schema_parsing import ByconSchemas

################################################################################

class MultiQueryResponses:
    def __init__(self, dataset_id=None):
        multiqueries = {"ByconQuery": {}}
        if "testqueries" in BYC_PARS.get("mode", "").lower():
            multiqueries = BYC.get("test_queries")
        self.entity_ids = set()
        self.target_path_id = "biosamples"
        self.multiqueries = multiqueries
        self.ds_id = dataset_id

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def get_analysis_ids(self):
        self.target_path_id = "analyses"
        self.__run_multi_queries()
        return self.entity_ids


    # -------------------------------------------------------------------------#

    def get_biosample_ids(self):
        self.target_path_id = "biosamples"
        self.__run_multi_queries()
        return self.entity_ids


    # -------------------------------------------------------------------------#

    def get_individual_ids(self):
        self.target_path_id = "individuals"
        self.__run_multi_queries()
        return self.entity_ids


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __run_multi_queries(self):
        ho_id = f'{self.target_path_id}.id'
        for qek, qev in self.multiqueries.items():
            for p, v in qev.items():
                BYC_PARS.update({p: v})
            BRS = ByconResultSets()
            ds_results = BRS.datasetsResults()

            # clean out those globals for next run
            for p, v in qev.items():
                BYC_PARS.pop(p)
            
            if not (ds := ds_results.get(self.ds_id)):
                r_c = BRS.get_record_queries()
                BYC["ERRORS"].append(f'ERROR - no {qek} data for {self.ds_id}')
                continue
            f_i_ids = ds[ho_id].get("target_values", [])
            self.entity_ids = set(self.entity_ids)
            self.entity_ids.update(random_samples(f_i_ids, min(BYC_PARS.get("limit", 200), len(f_i_ids))))
            BYC["NOTES"].append(f'{qek} with {ds[ho_id].get("target_count", 0)} {self.target_path_id} hits')
            self.entity_ids = list(self.entity_ids)


################################################################################

class BeaconResponseMeta:
    def __init__(self, data_response=None):
        self.beacon_schema = BYC["response_entity"].get("beacon_schema", "___none___")
        self.entity_defaults = BYC.get("entity_defaults", {})
        self.response_meta = ByconSchemas("beaconResponseMeta", "").get_schema_instance()
        self.returned_granularity = BYC.get("returned_granularity", "boolean")
        self.data_response = data_response
        self.record_queries = None
        self.filters = ByconFilters().get_filters()

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
        r_m.update({"returned_granularity": self.returned_granularity})

        info = self.entity_defaults["info"].get("content", {"api_version": "___none___"})
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

        fs = self.filters
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

        info = self.entity_defaults["info"].get("content", {"api_version": "___none___"})
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
        self.error_response = ByconSchemas("beaconErrorResponse", "").get_schema_instance()
        self.meta = BeaconResponseMeta().populatedMeta()


    # -------------------------------------------------------------------------#

    def respond_if_errors(self, error_code=422):
        if len(errors := BYC.get("ERRORS", [])) < 1:
            return False
        self.error_response.update({
            "error": {"error_code": error_code, "error_message": ", ".join(errors)},
            "meta": self.meta
        })
        print_json_response(self.error_response, error_code)


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
        self.data_response = ByconSchemas("beaconInfoResponse", "").get_schema_instance()
        self.data_response.update({"meta": BeaconResponseMeta().populatedMeta() })
        self.info_response_content = {}
    

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
            c_f = ByconSchemas("beaconConfiguration").get_schema_file_path()
            self.info_response_content = load_yaml_empty_fallback(c_f)
            return
        if "beaconMap" in self.response_entity_id:
            c_f = ByconSchemas("beaconMap").get_schema_file_path()
            self.info_response_content = load_yaml_empty_fallback(c_f)
            return
        if "entryType" in self.response_entity_id:
            c_f = ByconSchemas("beaconConfiguration").get_schema_file_path()
            e_t_s = load_yaml_empty_fallback(c_f)
            self.info_response_content = {"entry_types": e_t_s["entryTypes"] }
            return
        if "info" in self.response_entity_id:
            info = self.entity_defaults.get("info", {})
            pgx_info = info.get("content", {})
            beacon_info = ByconSchemas("beaconInfoResults", "").get_schema_instance()
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
            if e_d.get("is_beacon_entity", False) is True and e_t not in ets:
                beacon_schemas.append(e_d.get("beacon_schema", {}))
                ets.add(e_t)
            else:
                prdbug(f'... skipping {e_t} schema')

        self.data_response.update( { "returned_schemas": beacon_schemas } )


################################################################################

class BeaconDataResponse:
    def __init__(self):
        self.user_name = BYC.get("USER", "anonymous")
        self.include_handovers = BYC_PARS.get("include_handovers", False)
        self.response_entity_id = BYC.get("response_entity_id")
        self.returned_granularity = BYC.get("returned_granularity", "boolean")
        self.beacon_schema = BYC["response_entity"].get("beacon_schema", "___none___")
        self.record_queries = {}
        self.response_schema = BYC.get("response_schema", "___none___")
        self.data_response = ByconSchemas(BYC["response_schema"], "").get_schema_instance()
        self.data_response.update({"meta": BeaconResponseMeta(self.data_response).populatedMeta() })
        for m in ["beacon_handovers", "info"]:
            self.data_response.pop(m, None)
        self.data_time_init = datetime.now()
    

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def dataResponseFromEntry(self):
        rp_id = self.response_entity_id
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

        self.result_sets_start = datetime.now()
        BRS = ByconResultSets()
        self.result_sets, self.record_queries = BRS.get_populated_result_sets()
        self.dataset_results = BRS.datasetsResults()
        self.__acknowledge_HIT()
        self.__acknowledge_MISS()
        self.data_response["response"].update({"result_sets": self.result_sets})
        self.__resultset_response_update_summaries()
        # self.__resultset_response_add_aggregations()
        self.__resultSetResponse_force_autorized_granularities()

        if not self.data_response.get("info"):
            self.data_response.pop("info", None)

        self.__response_clean_parameters()
        self.__check_switch_to_error_response()
        self.result_sets_end = datetime.now()
        self.result_sets_duration = self.result_sets_end - self.result_sets_start

        self.data_response.update({"meta": BeaconResponseMeta(self.data_response).populatedMeta(self.record_queries) })

        dbm = f'... data response duration was {self.result_sets_duration.total_seconds()} seconds'

        return self.data_response


    # -------------------------------------------------------------------------#

    def collectionsResponse(self):
        if not "beaconCollectionsResponse" in self.response_schema:
            return

        self.colls, self.queries = ByconCollections().populatedCollections()
        self.__collections_response_remap_cohorts()
        self.data_response["response"].update({"collections": self.colls})
        self.record_queries.update({"entities": self.queries})
        self.__collections_response_update_summaries()
        self.__check_switch_to_error_response()
        self.data_response.update({"meta": BeaconResponseMeta(self.data_response).populatedMeta(self.record_queries) })
        self.data_response.get("meta", {}).get("received_request_summary", {}).pop("include_resultset_responses", None)
        return self.data_response


    # -------------------------------------------------------------------------#

    def filteringTermsResponse(self):
        if not "beaconFilteringTermsResponse" in self.response_schema:
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

    def filteringTermsList(self):
        if not "beaconFilteringTermsResponse" in self.response_schema:
            return
        fts, ress, query = ByconFilteringTerms().populatedFilteringTerms()
        return fts


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
        if "boolean" in self.returned_granularity:
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

    def __collections_response_remap_cohorts(self):
        if not "cohort" in BYC.get("response_entity_id", "___none___"):
            return
        pop_keys = ["_id", "frequencymap", "child_terms", "code_matches", "count", "dataset_id", "db_key", "namespace_prefix", "type", "collation_type", "hierarchy_paths", "parent_terms", "scope"]
        for c in self.colls:
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


    # -------------------------------------------------------------------------#

    def __response_clean_parameters(self):
        r_m = self.data_response.get("response", {})
        r_m.pop("$schema", None)


    # -------------------------------------------------------------------------#

    def __resultset_response_update_summaries(self):
        if not "beaconResultsetsResponse" in self.response_schema:
            return
        t_count = 0
        t_exists = False
        for r_s in self.data_response.get("response", {}).get("result_sets", []):
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

 
    # -------------------------------------------------------------------------#

    def __collections_response_update_summaries(self):
        if not "beaconCollectionsResponse" in self.response_schema:
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
    def __init__(self, dataset_id=None):
        self.response_entity_id = BYC.get("response_entity_id", "filteringTerm")
        self.ft_instance = ByconSchemas("beaconFilteringTermsResults", "$defs/FilteringTerm").get_schema_instance()
        self.data_collection = "collations"
        self.filter_collation_types = set()
        self.filtering_terms = []
        self.filter_resources = []
        self.filtering_terms_query = {}
        self.ds_id = BYC["BYC_DATASET_IDS"][0] if dataset_id is None else dataset_id
        self.special_mode = BYC_PARS.get("mode", "___none___")
        self.filter_id_match_mode = "full"
        self.filters = ByconFilters().get_filters()

        def_keys = self.ft_instance.get("default", self.ft_instance.keys())
        if "termTree" in self.special_mode:
            def_keys = ["id", "label", "count", "hierarchy_paths", "cnv_analyses", "collation_type"]

        self.delivery_keys = BYC_PARS.get("delivery_keys", def_keys)

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def populatedFilteringTerms(self):
        self.__filtering_terms_query()
        self.__return_filtering_terms()
        self.__return_filter_resources()
        return self.filtering_terms, self.filter_resources, self.filtering_terms_query


    # -------------------------------------------------------------------------#

    def filteringTermsList(self):
        self.__filtering_terms_query()
        self.__return_filtering_terms()
        return self.filtering_terms


    # -------------------------------------------------------------------------#

    def filteringTermsIdList(self):
        self.__filtering_terms_query()
        self.__return_filtering_terms()
        return [x.get("id") for x in self.filtering_terms]


    # -------------------------------------------------------------------------#

    def get_query(self):
        self.__filtering_terms_query()
        return self.filtering_terms_query


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __filtering_terms_query(self):
        query = {}
        q_list = []
        ft_fs = []
        f_re = None

        if "start" in self.filter_id_match_mode:
            for f in self.filters:
                ft_fs.append('(' + f.get("id", "___none___") + ')')
            if len(ft_fs) > 0:
                f_s = '|'.join(ft_fs)
                f_re = re.compile(r'^' + '|'.join(ft_fs))

            # construction of a start-anchored regex query for multiple partial
            # filter id matches (non-standard; e.g. for autocompletes or custom
            # lookups)
            if f_re:
                q_list.append({"id": {"$regex": f_re}})

        elif len(self.filters) > 0:
            q_list.append({"id": {"$in": [f.get("id") for f in self.filters]}})

        if len(q_types := BYC_PARS.get("collation_types", [])) > 0:
            q_list.append({"collation_type": {"$in": q_types }})
        elif not "withpubmed" in self.special_mode:
            q_list.append({"collation_type": {"$not": {"$regex":"pubmed"}}})

        if len(q_list) == 1:
            query = q_list[0]
        elif len(q_list) > 1:
            query = {"$and": q_list}

        if BYC["TEST_MODE"] is True:
            query = mongo_test_mode_query(self.ds_id, self.data_collection)

        # prdbug(f'filtering_terms_query: {query}')

        self.filtering_terms_query = query


    # -------------------------------------------------------------------------#

    def __return_filtering_terms(self):
        fields = {"_id": 0}
        for k in self.delivery_keys:
            fields.update({k: 1})
        if "collation_type" not in fields:
            fields.update({"collation_type": 1})

        f_s = mongo_result_list(self.ds_id, self.data_collection, self.filtering_terms_query, fields)
        t_f_t_s = []
        for f in f_s:
            self.filter_collation_types.add(f.get("collation_type", None))
            if "collation_type" not in self.delivery_keys:
                f.pop("collation_type", None)
            t_f_t_s.append(f)

        self.filtering_terms = t_f_t_s


    # -------------------------------------------------------------------------#

    def __return_filter_resources(self):
        r_o = {}
        f_d_s = BYC["filter_definitions"].get("$defs", {})
        collation_types = list(self.filter_collation_types)
        res_schema = ByconSchemas("beaconFilteringTermsResults", "$defs/Resource").get_schema_instance()
        for c_t in collation_types:
            if c_t not in f_d_s:
                continue
            f_d = f_d_s[c_t]
            if not "ontologyTerm" in f_d.get("type"):
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
        self.__datasets_update_latest_stats()
        self.collections_queries.update({"datasets":{}})


    # -------------------------------------------------------------------------#

    def __datasets_update_latest_stats(self):
        stat = list(ByconInfo().beaconinfo_get_latest())
        if len(stat) < 1:
            ds_stats = {}
        ds_stats = stat[0].get("datasets", {})

        for coll_id, coll in BYC["dataset_definitions"].items():
            prdbug(f'... processing dataset {coll_id} => {BYC.get("BYC_DATASET_IDS", [])}')
            if not coll_id in BYC.get("BYC_DATASET_IDS", []):
                continue
            if (ds_vs := ds_stats.get(coll_id)):
                if "filtering_terms" in BYC["response_entity_id"]:
                    coll.update({ "filtering_terms": []})
                    coll_items = ds_vs.get("collations", {})
                    for c_id, c_v in ds_vs.get("collations", {}).items():
                        coll["filtering_terms"].append({"id":c_id, "label": c_v.get("label", c_id)})
            # TODO: update counts
            # TODO: remove verifier hack
            for t in ["createDateTime", "updateDateTime"]:
                d = str(coll.get(t, "1967-11-11"))
                if re.match(r'^\d\d\d\d\-\d\d\-\d\d$', d):
                    coll.update({t:f'{d}T00:00:00+00:00'})
            self.collections.append(coll)

    # -------------------------------------------------------------------------#

    def __collections_return_cohorts(self):
        if not "cohort" in self.response_entity_id:
            return

        # TODO: reshape cohorts according to schema
        query = { "collation_type": "pgxcohort" }
        limit = 0
        if BYC["TEST_MODE"] is True:
            limit = BYC_PARS.get("test_mode_count", 5)
        else:
            c_q = BYC_PARS.get("filters", [])
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
                self.collections.append(cohort)

        self.collections_queries.update({"cohorts":query})


################################################################################

class ByconResultSets:
    def __init__(self):
        self.datasets_results = dict()  # the object with matched ids per dataset, per h_o
        self.datasets_data = dict()     # the object with data of requested entity per dataset
        self.result_sets = list()       # data rewrapped into the resultSets list
        self.flattened_data = list()    # data from all resultSets as flat list
        self.entity_defaults = BYC.get("entity_defaults", {})
        self.response_entity_id = BYC.get("response_entity_id", "biosample")
        self.returned_granularity = BYC.get("returned_granularity", "boolean")
        self.aggregation_terms = BYC_PARS.get("aggregation_terms", [])
        self.limit = BYC_PARS.get("limit")
        self.skip = BYC_PARS.get("skip")
        self.mongo_client = MongoClient(host=DB_MONGOHOST)

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
        self.__populate_result_sets()
        self.__result_sets_save_handovers()
        return self.result_sets, self.record_queries


    # -------------------------------------------------------------------------#

    def get_flattened_data(self):
        self.__retrieve_datasets_data()

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

    def dataset_results_analysis_ids(self, ds_id="___none___"):
        analysis_ids = set()
        self.response_entity_id = "analysis"
        self.__retrieve_datasets_data()
        if not ds_id in self.datasets_data:
            BYC["ERRORS"].append("no correct dataset id provided to `dataset_results_biosample_ids`")
            return []

        data = self.datasets_data[ds_id]
        for s in data:
            if (ana_id := s.get("analysis_id")):
                analysis_ids.add(ana_id)

        return list(analysis_ids)


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __get_handover_access_key(self):
        e_d_s = self.entity_defaults.get(self.response_entity_id, {})
        coll = e_d_s.get("collection", "___none___")
        self.handover_key = f'{coll}.id'
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
        r_set = ByconSchemas("beaconResultsets", "$defs/ResultsetInstance").get_schema_instance()
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
        ds_r_start = datetime.now()
        for i, r_set in enumerate(self.result_sets):
            ds_id = r_set.get("id", "___none___")
            DR = ByconDatasetResults(ds_id, self.record_queries)
            ds_res = DR.retrieveResults()
            self.datasets_results.update({ds_id: ds_res})            
        ds_r_duration = datetime.now() - ds_r_start
        
        dbm = f'... datasets results querying needed {ds_r_duration.total_seconds()} seconds'
        prdbug(dbm)
        return


    # -------------------------------------------------------------------------#

    def __retrieve_datasets_data(self):
        ds_d_start = datetime.now()
        for ds_id in self.datasets_results.keys():
            self.__retrieve_single_dataset_data(ds_id)
        ds_d_duration = datetime.now() - ds_d_start
        dbm = f'... datasets data retrieval needed {ds_d_duration.total_seconds()} seconds'
        prdbug(dbm)


    # -------------------------------------------------------------------------#

    def __retrieve_single_dataset_data(self, ds_id):
        if not (ds_results := self.datasets_results.get(ds_id)):
            return
        if not self.handover_key in ds_results.keys():
            return
        res = ds_results.get(self.handover_key, {})
        q_coll = res.get("collection", "___none___")
        q_v_s = res.get("target_values", [])
        q_v_s = return_paginated_list(q_v_s, self.skip, self.limit)

        data_coll = self.mongo_client[ds_id][q_coll]

        r_s_res = []
        for q_v in q_v_s:
            o = data_coll.find_one({"id": q_v })
            r_s_res.append(o)
        self.datasets_data.update({ds_id: r_s_res})


    # -------------------------------------------------------------------------#

    def __populate_result_sets(self):
        ds_v_start = datetime.now()
        for i, r_set in enumerate(self.result_sets):
            ds_id = r_set["id"]
            ds_res = self.datasets_results.get(ds_id)
            if not ds_res:
                continue

            r_set.update({"results_handovers": dataset_response_add_handovers(ds_id, self.datasets_results)})

            # avoiding summary generation for boolean responses
            if not "boolean" in self.returned_granularity:
                if (s_r := self.__dataset_response_add_aggregations(ds_id, ds_res)):
                    r_set.update({"summary_results": s_r})

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
                entity = h_o.get("entity_id", "___none___")
                if entity == self.response_entity_id:
                    rs_c = h_o["target_count"]
            self.result_sets[i].update({
                "info": info,
                "response_entity_id" : self.response_entity_id,
                "results_count": rs_c,
                "exists": True if rs_c > 0 else False,
                "results": r_s_res
            })
        ds_v_duration = datetime.now() - ds_v_start
        dbm = f'... __populate_result_sets needed {ds_v_duration.total_seconds()} seconds'
        prdbug(dbm)
        return

    # -------------------------------------------------------------------------#

    def __dataset_response_add_aggregations(self, ds_id, ds_res):
        prdbug(f'... __resultset_response_add_aggregations for dataset {ds_id} - aggregation_terms: {self.aggregation_terms}')

        self.__set_available_aggregation_ids(ds_id)

        s_r = []
        # CNV frequencies; only returned for `/analyses`
        if (cnv_f := self.__analyses_cnvfrequencies(ds_id, ds_res)):
            s_r.append(cnv_f)

        return s_r


    # -------------------------------------------------------------------------#

    def __set_available_aggregation_ids(self, ds_id):

        """
        This function sets the available aggregation ids based on the
        aggregation_terms and response_entity_id.
        """

        self.available_aggregation_ids = set(self.aggregation_terms)

        if len(self.available_aggregation_ids) > 0:
            ft_original = BYC_PARS.get("filters", [])
            BYC_PARS.update({"filters": []})
            coll_ids = ByconFilteringTerms(ds_id).filteringTermsIdList()
            BYC_PARS.update({"filters": ft_original})

            self.available_aggregation_ids = self.available_aggregation_ids & set(coll_ids)


        # temporary home for specials ... 
        if "cnvfrequencies" in self.aggregation_terms and "analysis" in self.response_entity_id:
            self.available_aggregation_ids.add("cnvfrequencies")

        self.available_aggregation_ids = list(self.available_aggregation_ids)
        prdbug(f'__set_available_aggregation_ids: {self.available_aggregation_ids}')


    # -------------------------------------------------------------------------#

    def __analyses_cnvfrequencies(self, ds_id, ds_res):
        if not "cnvfrequencies" in self.available_aggregation_ids:
            return False

        analyses_result = ds_res.get("analyses.id", {})
        BSUM = ByconSummary()
        int_f = BSUM.analyses_frequencies_bundle(ds_id, analyses_result)
        d = int_f.get("interval_frequencies", [])
        c = int_f.get("sample_count", 0)
        return {
            "id": "cnvfrequencies",
            "entity": "analysis",
            "distribution": {
                "items":d,
            },
            "description": f'Binned CNV frequencies for {c} matched analyses',
            "count": c
        }


################################################################################
# common response functions ####################################################
################################################################################

def print_json_response(this={}, status_code=200):
    if not "___shell___" in ENV:
        print(f'Status: {status_code}')
        print('Content-Type: application/json')
        print()

    # There are some "do not camelize" exceptions downstream
    prjsoncam(this) 
    print()
    exit()


################################################################################

def print_text_response(this="", status_code=200):
    if not "___shell___" in ENV:
        print(f'Status: {status_code}')
        print('Content-Type: text/plain')
        print()

    print(this)
    print()
    exit()


################################################################################

def print_html_response(this="", status_code=200):
    if not "___shell___" in ENV:
        print(f'Status: {status_code}')
        print('Content-Type: text/html')
        print()

    print(this)
    print()
    exit()


################################################################################

def print_uri_rewrite_response(uri=""):
    print("Status: 302")
    print(f'Location: {uri}')
    print()
    exit()

