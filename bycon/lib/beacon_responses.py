import json, requests, sys, yaml
from datetime import datetime
from deepmerge import always_merger
from os import environ, pardir, path
from random import sample as random_samples

from config import *

from bycon_helpers import *
from bycon_info import ByconInfo
from parameter_parsing import ByconFilters, ByconParameters
from query_execution import ByconDatasetResults # execute_bycon_queries
from query_generation import ByconQuery, CollationQuery
from response_remapping import *
from schema_parsing import ByconSchemas, RecordsHierarchy

################################################################################

class BeaconResponseMeta:
    def __init__(self, data_response=None):
        self.beacon_schema = BYC["response_entity"].get("defaultSchema", "___none___")
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
        if self.record_queries:
            self.response_meta.update({"info": always_merger.merge(self.response_meta.get("info", {}), {"original_queries": self.record_queries})})
        if "returned_schemas" in self.response_meta:
            self.response_meta.update({"returned_schemas":[self.beacon_schema]})

        if not (r_r_s := self.response_meta.get("received_request_summary")):
            return

        if BYC["TEST_MODE"] is True:
            r_r_s.update({"test_mode": BYC["TEST_MODE"]})

        r_r_s.update({
            "requested_schemas": [self.beacon_schema],
            "pagination": {"skip": BYC_PARS.get("skip"), "limit": BYC_PARS.get("limit")},
            "dataset_ids": BYC["BYC_DATASET_IDS"]
        })

        fs_p = []
        if len(self.filters) > 0:
            for f in self.filters:
                if (f_id := f.get("id")):
                    fs_p.append(f_id)
        if len(fs_p) > 0:
            r_r_s.update({"filters": self.filters})
        else:
            r_r_s.pop("filters", None)

        for p in ["include_resultset_responses", "requested_granularity"]:
            if p in BYC_PARS and p in r_r_s:
                r_r_s.update({p: BYC_PARS.get(p)})

        if r_r_s.get("request_parameters"):
            r_r_s["request_parameters"].pop("$schema", None)
        for q in ["cohort_ids", "cyto_bands", "chro_bases"]:
            if q in BYC_PARS:
                r_r_s.update({"request_parameters": always_merger.merge( r_r_s.get("request_parameters", {}), { q: BYC_PARS.get(q) })})

        if not r_r_s.get("request_parameters"):
            r_r_s.pop("request_parameters", None)

        info = self.entity_defaults["info"].get("content", {})
        for p in ["api_version", "beacon_id"]:
            r_r_s.update({p: info.get(p, "___none___")})

        self.response_meta.update({"received_request_summary": r_r_s})


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
        self.beacon_schema = BYC["response_entity"].get("defaultSchema", "___none___")
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
            # c_f = ByconSchemas("beaconConfiguration").get_schema_file_path()
            # self.info_response_content = load_yaml_empty_fallback(c_f)
            self.info_response_content = BYC.get("beacon_configuration", {})
            betks = []
            for e_t, e_d in self.entity_defaults.items():
                if e_d.get("is_beacon_entity", False) is True:
                    betks.append(e_t)
            bet = {}
            for k in sorted(betks):
                bet.update({k: self.entity_defaults.get(k, {})})
            self.info_response_content.update({"entry_types": bet})
            return
        if "beaconMap" in self.response_entity_id:
            b_m = BYC.get("beacon_map", {})
            b_m = dict_replace_values(b_m, "___BEACON_ROOT___", BEACON_ROOT)
            self.info_response_content = b_m
            return
        if "entryType" in self.response_entity_id:
            e_t_s = BYC.get("beacon_configuration", {})
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
                beacon_schemas.append(e_d.get("defaultSchema", {}))
                ets.add(e_t)
            else:
                prdbug(f'... skipping {e_t} schema')

        self.data_response.update( { "returned_schemas": beacon_schemas } )



################################################################################
################################################################################
################################################################################

class BeaconDataResponse:
    def __init__(self):
        self.user_name = BYC.get("USER", "anonymous")
        self.include_handovers = BYC_PARS.get("include_handovers", False)
        self.response_entity_id = BYC.get("response_entity_id")
        self.returned_granularity = BYC.get("returned_granularity", "boolean")
        self.beacon_schema = BYC["response_entity"].get("defaultSchema", "___none___")
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

        if self.response_entity_id and "dataset" in self.response_entity_id:
            if t_count == 1 and "aggregated" in self.returned_granularity:
                BA = ByconAggregations(BYC["BYC_DATASET_IDS"][0])        
                self.data_response["response"]["collections"][0].update({
                    "summary_results": BA.datasetAllAggregation()
                })

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
            # this handles test mode, too...
            query = CollationQuery().getQuery()

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
        f_d_s = BYC.get("filter_definitions", {}).get("$defs", {})
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
        self.queried_entities = RecordsHierarchy().entities()
        coll_id = f'{self.response_entity_id}_coll'
        self.data_collection = BYC_DBS.get(coll_id, "collations")
        self.collections = []
        self.collections_queries = {}
        self.mongo_client = MongoClient(host=BYC_DBS["mongodb_host"])


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
        # stat = list(ByconInfo().beaconinfo_get_latest())
        # if len(stat) < 1:
        #     ds_stats = {}
        # ds_stats = stat[0].get("datasets", {})

        for coll_id, coll in BYC["dataset_definitions"].items():
            prdbug(f'... processing dataset {coll_id} => {BYC.get("BYC_DATASET_IDS", [])}')
            if not coll_id in BYC.get("BYC_DATASET_IDS", []):
                continue

            counts = {}
            for e in self.queried_entities:
                coll_name = BYC_DBS.get(f'{e}_coll', '___none___')
                d_c = self.mongo_client[coll_id][coll_name]
                counts.update({e: d_c.count_documents({}) })

            coll.update({"counts": counts})

            # if (ds_vs := ds_stats.get(coll_id)):
            #     if "filtering_terms" in BYC["response_entity_id"]:
            #         coll.update({ "filtering_terms": []})
            #         coll_items = ds_vs.get("collations", {})
            #         for c_id, c_v in ds_vs.get("collations", {}).items():
            #             coll["filtering_terms"].append({"id":c_id, "label": c_v.get("label", c_id)})
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

        mongo_client = MongoClient(host=BYC_DBS["mongodb_host"])
        for ds_id in BYC["BYC_DATASET_IDS"]:
            mongo_db = mongo_client[ ds_id ]        
            mongo_coll = mongo_db[ "collations" ]
            for cohort in mongo_coll.find( query, limit=limit ):
                self.collections.append(cohort)

        self.collections_queries.update({"cohorts":query})


################################################################################
################################################################################
################################################################################

class ByconAggregations:
    def __init__(self, ds_id=None):
        self.dataset_id = ds_id
        self.aggregation_terms = BYC_PARS.get("aggregation_terms", [])
        self.aggregator_definitions = BYC.get("aggregator_definitions", {}).get("$defs", {})
        self.dataset_aggregation = [] 
        self.mongo_client = MongoClient(host=BYC_DBS["mongodb_host"])
        self.data_client = self.mongo_client[ds_id]
        self.term_coll = self.data_client["collations"]


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def datasetResultAggregation(self, dataset_result={}):
        self.dataset_result = dataset_result

        # CAVE: Always aggregating on biosamples
        self.__aggregate_dataset_data(use_dataset_result=True)

        return self.dataset_aggregation


    # -------------------------------------------------------------------------#

    def datasetAllAggregation(self):
        self.__aggregate_dataset_data()
        return self.dataset_aggregation


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __aggregate_dataset_data(self, query={}, use_dataset_result=False):
        # temporary aggregation implementation
        # WiP
        # TODO: 2-dimensional with buckets; they need another way - e.g. $switch
        # https://www.mongodb.com/docs/manual/reference/operator/aggregation/switch/


        agg_terms = self.aggregator_definitions.keys()
        if len(self.aggregation_terms) > 0:
            agg_terms = list(set(agg_terms) & set(self.aggregation_terms))

        # one could aggregate all terms in one pipeline, but this is clearer
        for a_k in agg_terms:
            a_v = self.aggregator_definitions.get(a_k)
            if use_dataset_result:
                concepts = a_v.get("concepts", [])
                scope, concept = concepts[0].get("property", "___none___.___none___").split('.', 1)
                coll = BYC_DBS.get(f"{scope}_coll", "___none___")
                if not (coll_k := f"{coll}.id") in self.dataset_result.keys():
                    continue
                res = self.dataset_result.get(coll_k, {})
                q_v_s = res.get("target_values", [])
                query = {"id": {"$in": q_v_s}}
                prdbug(f'... aggregating {a_k} for {coll_k} with query {query}')

            a_v.update({"distribution": []})    
            self.__aggregate_single_concept(a_k, a_v, query)
            # self.__aggregate_single_concept_buckets(a_k, a_v, query)
            self.__aggregate_2_concepts(a_k, a_v, query)


    # -------------------------------------------------------------------------#

    def __aggregate_single_concept(self, a_k, a_v, query={}):
        concepts = a_v.get("concepts", [])
        if len(concepts) != 1:
            return

        scope, concept_id = concepts[0].get("property", "___none___.___none___").split('.', 1)
        if not (collection := BYC_DBS.get(f"{scope}_coll")):
            return

        data_coll = self.data_client[collection]

        _id = self.__id_object(a_k, concepts[0])

        agg_p = [ { "$match": query } ]
        agg_p.append(            
            { "$group": {
                    "_id": _id,
                    "count": { "$sum": 1 }
                }
            }        
        )
        # sorting either on logical order () detection order
        if a_v.get("sorted") is True:
            agg_p.append({ "$sort": { "_id.order": 1 } })
        else:
            agg_p.append({ "$sort": { "count": -1 } })

        agg_d = data_coll.aggregate(agg_p)

        # label lookups only for term-based aggregations
        for a in agg_d:
            # prjsonnice(a)
            if not (i_k := a.get("_id")):
                continue
            if type(i_k) is dict and "id" in i_k:
                id_v = i_k.get("id")
                label = i_k.get("label", id_v)
            else:
                id_v = i_k
                label = id_v
                if (coll := self.term_coll.find_one( {"id": i_k})):
                    label = coll.get("label", id_v)
            a_v["distribution"].append({
                "concept_values": [
                    {"id": id_v, "label": label}
                ],
                "count": a.get("count", 0)
            })

        self.dataset_aggregation.append(a_v)


    # -------------------------------------------------------------------------#

    def __aggregate_2_concepts(self, a_k, a_v, query={}):
        concepts = a_v.get("concepts", [])
        if len(concepts) != 2:
            return

        # TODO: more than 2 (loop) and $lookup for different collection

        d_one, c_one = concepts[0].get("property", "___none1___.___none1___").split('.', 1)
        d_two, c_two = concepts[1].get("property", "___none2___.___none2___").split('.', 1)
        if d_one != d_two:
            return

        if not (collection := BYC_DBS.get(f"{d_one}_coll")):
            return
        data_coll = self.data_client[collection]

        agg_p = [
            { "$match": query },
            { "$group":
                {
                    "_id": {
                        c_one.replace(".", "_"): self.__id_object(a_k, concepts[0]),
                        c_two.replace(".", "_"): self.__id_object(a_k, concepts[1])
                    },
                    "count": { "$sum": 1 }
                }
            },
            { "$sort": { "count": -1 } }
        ]
        agg_d = list(data_coll.aggregate(agg_p))

        if len(agg_d) < 1:
            return

        if a_v.get("sorted") is True:
            k = list(agg_d[0]["_id"].keys())[0]
            if "order" in agg_d[0]["_id"][k]:
                agg_d = sorted(agg_d, key=lambda x: x["_id"][k].get("order", 9999))

        # label lookups only for term-based aggregations
        for a in agg_d:
            if not (i_k := a.get("_id")):
                continue
            c_v_s = []
            id_v_s = list(i_k.values())
            for v in id_v_s:
                if type(v) is dict and "id" in v:
                    label = v.get("label", v.get("id"))
                    c_v_s.append({"id": v.get("id"), "label": label})
                    continue
                label = v
                if (coll := self.term_coll.find_one( {"id": v})):
                    label = coll.get("label", label)
                    c_v_s.append({"id": v, "label": label})

            a_v["distribution"].append({
                "concept_values": c_v_s,
                "count": a.get("count", 0)
            })

        self.dataset_aggregation.append(a_v)


    # -------------------------------------------------------------------------#

    def __id_object(self, a_k, concept):
        if (_id := self.__switch_branches_from_terms(a_k, concept)):
            return _id
        if (_id := self.__switch_branches_from_splits(a_k, concept)):
            return _id
        scope, concept_id = concept.get("property", "___none___.___none___").split('.', 1)
        return f"${concept_id}"


    # -------------------------------------------------------------------------#

    def __switch_branches_from_terms(self, a_k, concept):
        """
        Switch example for term list from children:

        ```
        db.biosamples.aggregate([
            { $group: {
                "_id": {
                    "cancerType": {
                        $switch: {
                            "branches": [
                                { "case": { $in: [ "$histological_diagnosis.id", ["NCIT:C3466", "NCIT:C3457", "NCIT:C3163"] ]}, "then": {"id": "...", "label": "Some Lymphoma"} },
                                { "case": { $in: [ "$histological_diagnosis.id", ["NCIT:C3512", "NCIT:C3493"] ]}, "then": {"id": "...", "label": "Some Lung Cancer"} }
                            ],
                            "default": {"id": "other", "label": "other"}
                        }
                    }
                },
                "count": { $sum: 1 }
            }}
        ])
        ```
        """

        if len(terms := concept.get("termIds", [])) < 1:
            return False

        scope, concept_id = concept.get("property", "___none___.___none___").split('.', 1)

        branches = []
        for d_i, i_k in enumerate(terms):
            if not (coll := self.term_coll.find_one( {"id": i_k})):
                continue
            label = coll.get("label", i_k)
            if len(child_terms := coll.get("child_terms", [])) < 1:
                continue
            branches.append({
                "case": { "$in": [ f'${concept_id}', child_terms ] },
                "then": {"id": i_k, "label": label, "order": d_i}
            })

        # fallback dummy branch - at least one is needed or error
        if len(branches) < 1:
            branches.append({
                "case": { "$in": [f'${concept_id}', [ "___undefined___" ]] },
                "then": {"id": "undefined", "label": "undefined", "order": 1}
            })

        _id = {
            "$switch": {
                "branches": branches,
                "default": {"id": "other", "label": "other", "order": len(terms)}
            }
        }

        return _id


    # -------------------------------------------------------------------------#

    def __switch_branches_from_splits(self, a_k, concept):
        """
        Numeric splits can be implemented using `$bucket` or `$switch`. We're
        preferimg switches since they can be combined with other aggregators.

        Switch example for age at diagnosis buckets:

        ```
        db.biosamples.aggregate([
            { $group: {
                "_id": {
                    "ageAtDiagnosis": {
                        $switch: {
                            "branches": [
                                { "case": { $lt: [ "$individual_info.index_disease.onset.age_days", 365 ] }, "then": "<P1Y" },
                                { "case": { $lt: [ "$individual_info.index_disease.onset.age_days", 1825 ] }, "then": "<P5Y" },
=                               { "case": { $lt: [ "$individual_info.index_disease.onset.age_days", 14600 ] }, "then": "<P40Y" }
                            ],
                            "default": "undefined"
                        }
                    }
                },
                "count": { $sum: 1 }
            }}
        ])
        ```
        """
        if len(splits := concept.get("splits", [])) < 1:
            return False
        p = concept.get('property')
        f = concept.get('format', "")

        split_labs = splits
        split_vals = splits
        branches = []

        if "iso8601duration" in f:
            p = f"{p}_days"
            split_labs = ["unknown"]
            split_vals = [0]
            pre = "P0D"
            for l in splits:
                if re.match(r"^P\d", str(l)):
                    if int(d := days_from_iso8601duration(l)) > 0:
                        split_labs.append(f"[{pre}, {l})")
                        split_vals.append(d)
                    pre = l

        for d_i, d_l in enumerate(split_labs):
            branches.append({
                "case": { "$lt": [ f'${p}', split_vals[d_i] ] },
                "then": {"id": d_l, "label": d_l, "order": d_i}
            })

        _id = {
            "$switch": {
                "branches": branches,
                "default": {"id": "other", "label": "other", "order": len(split_labs)}
            }
        }

        return _id



################################################################################
################################################################################
################################################################################

class ByconResultSets:
    def __init__(self):
        self.datasets_results = dict()  # the object with matched ids per dataset, per h_o
        self.datasets_data = dict()     # the object with data of requested entity per dataset
        self.datasets_aggregations = dict()     # the object with aggregations of requested entity per dataset
        self.result_sets = list()       # data rewrapped into the resultSets list
        self.flattened_data = list()    # data from all resultSets as flat list
        self.entity_defaults = BYC.get("entity_defaults", {})
        self.response_entity_id = BYC.get("response_entity_id", "biosample")
        self.returned_granularity = BYC.get("returned_granularity", "boolean")
        self.limit = BYC_PARS.get("limit")
        self.skip = BYC_PARS.get("skip")
        self.mongo_client = MongoClient(host=BYC_DBS["mongodb_host"])

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
        coll = BYC_DBS.get(f"{self.response_entity_id}_coll", "___none___")
        self.handover_key = f'{coll}.id'


    # -------------------------------------------------------------------------#

    def __result_sets_save_handovers(self):
        ho_client = MongoClient(host=BYC_DBS["mongodb_host"])
        ho_coll = ho_client[BYC_DBS["housekeeping_db"]][BYC_DBS["handover_coll"]]
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
        prdbug('... retrieving datasets data')
        ds_d_start = datetime.now()
        for ds_id in self.datasets_results.keys():
            BA = ByconAggregations(ds_id)
            self.__retrieve_single_dataset_data(ds_id)
            self.datasets_aggregations.update({
                ds_id: BA.datasetResultAggregation(self.datasets_results[ds_id])
            })
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
        q_v_s = ByconH().paginated_list(q_v_s, self.skip, self.limit)

        prdbug(f'... retrieving data for dataset {ds_id}, collection {q_coll}, {len(q_v_s)} records')

        data_coll = self.mongo_client[ds_id][q_coll]

        r_s_res = []
        for q_v in q_v_s:
            o = data_coll.find_one({"id": q_v })
            r_s_res.append(o)
        self.datasets_data.update({ds_id: r_s_res})


    # -------------------------------------------------------------------------#

    def __populate_result_sets(self):
        ds_v_start = datetime.now()
        BHO = ByconHO()
        for i, r_set in enumerate(self.result_sets):
            ds_id = r_set["id"]
            ds_res = self.datasets_results.get(ds_id)
            if not ds_res:
                continue

            r_set.update({"results_handovers": BHO.get_dataset_handovers(ds_id, self.datasets_results)})

            q_c = ds_res.get("target_count", 0)

            info = {"counts": {}}
            rs_c = 0
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
                "exists": True if rs_c > 0 else False
            })
            prdbug(f'... populated result set for dataset {ds_id}, self.returned_granularity: {self.returned_granularity}, target_count: {q_c}')
            if self.returned_granularity == "record":
                r_s_res = self.datasets_data.get(ds_id, [])
                r_s_res = list(x for x in r_s_res if x)
                r_s_res = reshape_resultset_results(ds_id, r_s_res)
                self.result_sets[i].update({"results": r_s_res})
            if self.returned_granularity == "aggregated":
                self.result_sets[i].update({"summary_results": self.datasets_aggregations.get(ds_id, [])})

        ds_v_duration = datetime.now() - ds_v_start
        dbm = f'... __populate_result_sets needed {ds_v_duration.total_seconds()} seconds'
        prdbug(dbm)
        return


################################################################################
################################################################################
################################################################################

class ByconHO:
    def __init__(self):
        self.dataset_definitions = BYC.get("dataset_definitions", {})
        self.handover_types = BYC.get("handover_definitions", {}).get("h->o_types", {})
        self.response_entity_id = BYC.get("response_entity_id")


    #--------------------------------------------------------------------------#
    #----------------------------- public -------------------------------------#
    #--------------------------------------------------------------------------#

    def get_dataset_handovers(self, ds_id=None, datasets_results={}):
        self.dataset_handover = []
        self.dataset_id = ds_id
        if not (ds_def := self.dataset_definitions.get(str(ds_id))):
            return self.dataset_handover
        if not (ds_r := datasets_results.get(ds_id)):
            return self.dataset_handover
        self.dataset_results = ds_r

        ds_h_o = list(
            ds_def.get("handoverTypes", self.handover_types.keys()) & self.handover_types.keys()
        )

        for h_o_t in self.handover_types.keys():
            self.__process_handover(h_o_t)

        return self.dataset_handover


    #--------------------------------------------------------------------------#
    #----------------------------- private ------------------------------------#
    #--------------------------------------------------------------------------#

    def __process_handover(self, h_o_t):
        h_o_defs = self.handover_types.get(h_o_t)
        h_o_k = h_o_defs.get("h->o_key", "___none___")
        if not (h_o := self.dataset_results.get(h_o_k)):
            return
        if (target_count := h_o.get("target_count", 0)) < 1:
            return

        h_o_r = {
            "handover_type": h_o_defs.get("handoverType", {}),
            "info": {
                "content_id": h_o_t,
                "count": target_count
            },
            "note": h_o_defs.get("note", ""),
            "url": self.__handover_create_url(h_o_defs, h_o.get("id"))
        }

        # TODO: needs a new schema to accommodate this not as HACK ...
        # the phenopackets URL needs matched variants, which it wouldn't know about ...
        if "phenopackets" in h_o_t:
            if (v_access_id := self.dataset_results.get("variants.id", {}).get("id")):
                h_o_r["url"] += f'&variantsaccessid={v_access_id}'

        self.dataset_handover.append(h_o_r)


    #--------------------------------------------------------------------------#

    def __handover_create_url(self, h_o_defs, accessid):
        if not (addr := h_o_defs.get("script_path_web")):
            return ""
        url = f'{addr}?datasetIds={self.dataset_id}&accessid={accessid}'.replace("___BEACON_ROOT___", BEACON_ROOT)
        if "parvals" in h_o_defs:
            for pv_k, pv_v in h_o_defs["parvals"].items():
                url += f'&{pv_k}={pv_v}'
        return url


################################################################################
# common response functions ####################################################
################################################################################

def print_json_response(this={}, status_code=200):
    if "yaml" in BYC_PARS.get("mode", ""):
        print_yaml_response(this, status_code)
    if not "___shell___" in HTTP_HOST:
        print(f'Status: {status_code}')
        print('Content-Type: application/json')
        print()

    # There are some "do not camelize" exceptions downstream
    prjsoncam(this) 
    print()
    exit()


################################################################################

def print_yaml_response(this={}, status_code=200):
    if not "___shell___" in HTTP_HOST:
        print(f'Status: {status_code}')
        print('Content-Type: application/x-yaml')
        print()

    this = humps.camelize(this)
    print(yaml.dump(humps.camelize(this)))
    print()
    exit()


################################################################################

def print_text_response(this="", status_code=200):
    if not "___shell___" in HTTP_HOST:
        print(f'Status: {status_code}')
        print('Content-Type: text/plain')
        print()

    print(this)
    print()
    exit()


################################################################################

def print_html_response(this="", status_code=200):
    if not "___shell___" in HTTP_HOST:
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

