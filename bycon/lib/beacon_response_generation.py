from datetime import datetime
from deepmerge import always_merger
from os import environ

from bycon_helpers import mongo_result_list, mongo_test_mode_query, return_paginated_list
from cgi_parsing import prdbug
# from export_file_generation import *
from handover_generation import dataset_response_add_handovers
from query_execution import execute_bycon_queries
from query_generation import ByconQuery
from read_specs import datasets_update_latest_stats
from response_remapping import *
from variant_mapping import ByconVariant
from schema_parsing import object_instance_from_schema_name

################################################################################

class BeaconInfoResponse:
    """
    This response class is used for all the info / map / configuration responses
    which have the same type of `meta`.
    The responses are then provided by the dedicated methods
    """

    def __init__(self, byc: dict):
        self.debug_mode = byc.get("debug_mode", False)
        self.beacon_defaults = byc.get("beacon_defaults", {})
        self.entity_defaults = self.beacon_defaults.get("entity_defaults", {"info":{}})
        self.service_config = byc.get("service_config", {})
        self.response_schema = byc.get("response_schema", "beaconInfoResponse")
        self.beacon_schema = byc["response_entity"].get("beacon_schema", "___none___")
        self.data_response = object_instance_from_schema_name(byc, self.response_schema, "")
        self.error_response = object_instance_from_schema_name(byc, "beaconErrorResponse", "")
        info = self.entity_defaults["info"].get("content", {"api_version": "___none___"})
        r_m = self.data_response["meta"]
        for p in ["api_version", "beacon_id"]:
            if p in info.keys():
                r_m.update({p: info.get(p, "___none___")})
        if "returned_schemas" in r_m:
            r_m.update({"returned_schemas":[self.beacon_schema]})

        return
    

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def populatedInfoResponse(self, response={}):
        self.data_response.update({"response":response})
        return self.data_response


    # -------------------------------------------------------------------------#

    def errorResponse(self):
        return self.error_response


################################################################################

class BeaconDataResponse:

    def __init__(self, byc: dict):
        self.byc = byc
        self.test_mode = byc.get("test_mode", False)
        self.debug_mode = byc.get("debug_mode", False)
        self.beacon_defaults = byc.get("beacon_defaults", {})
        self.authorized_granularities = byc.get("authorized_granularities", {})
        self.user_name = byc.get("user_name", "anonymous")
        self.entity_defaults = self.beacon_defaults.get("entity_defaults", {"info":{}})
        self.form_data = byc.get("form_data", {})
        self.service_config = byc.get("service_config", {})
        self.response_schema = byc["response_schema"]
        self.returned_granularity = self.form_data.get("returned_granularity", "record")
        self.include_handovers = self.form_data.get("include_handovers", False)
        self.beacon_schema = byc["response_entity"].get("beacon_schema", "___none___")
        self.record_queries = {}
        self.data_response = object_instance_from_schema_name(byc, self.response_schema, "")
        self.error_response = object_instance_from_schema_name(byc, "beaconErrorResponse", "")
        self.warnings =[]
        self.data_time_init = datetime.datetime.now()

        return
    

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def resultsetResponse(self):
        dbm = f'... resultsetResponse start, schema {self.response_schema}'
        prdbug(dbm, self.debug_mode)
        if not "beaconResultsetsResponse" in self.response_schema:
            return

        self.result_sets_start = datetime.datetime.now()
        self.result_sets, self.record_queries = ByconResultSets(self.byc).populatedResultSets()

        self.data_response["response"].update({"result_sets": self.result_sets})
        self.__resultset_response_update_summaries()
        self.__resultSetResponse_force_granularities()


        b_h_o = self.data_response.get("beacon_handovers", [])
        if len(b_h_o) < 1:
            self.data_response.pop("beacon_handovers", None)
        if not b_h_o[0].get("id", None):
            self.data_response.pop("beacon_handovers", None)

        if not self.data_response.get("info"):
            self.data_response.pop("info", None)

        self.__check_switch_to_error_response()
        self.__meta_add_received_request_summary_parameters()
        self.__meta_add_parameters()
        self.__meta_clean_parameters()
        self.__response_clean_parameters()
        self.result_sets_end = datetime.datetime.now()
        self.result_sets_duration = self.result_sets_end - self.result_sets_start

        dbm = f'... data response duration was {self.result_sets_duration.total_seconds()} seconds'
        prdbug(dbm, self.debug_mode)

        return self.data_response


    # -------------------------------------------------------------------------#

    def collectionsResponse(self):
        if not "beaconCollectionsResponse" in self.response_schema:
            return

        colls, queries = ByconCollections(self.byc).populatedCollections()
        self.data_response["response"].update({"collections": colls})
        self.record_queries.update({"entities": queries})

        self.__collections_response_update_summaries()
        self.__check_switch_to_error_response()
        self.__meta_add_received_request_summary_parameters()
        self.__meta_add_parameters()
        self.__meta_clean_parameters()
        self.__response_clean_parameters()
        return self.data_response


    # -------------------------------------------------------------------------#

    def filteringTermsResponse(self):
        if not "beaconFilteringTermsResponse" in self.response_schema:
            return

        fts, ress, query = ByconFilteringTerms(self.byc).populatedFilteringTerms()
        self.data_response["response"].update({"filtering_terms": fts})
        self.data_response["response"].update({"resources": ress})
        self.record_queries.update({"entities": {"filtering_terms": query}})
        self.__check_switch_to_error_response()
        self.__meta_add_received_request_summary_parameters()
        self.__meta_add_parameters()
        self.__meta_clean_parameters()
        self.__response_clean_parameters()
        return self.data_response


    # -------------------------------------------------------------------------#

    def errorResponse(self, error=None):
        if type(error) is dict:
            self.error_response.update({"error": error})

        return self.error_response


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __check_switch_to_error_response(self):
        error = None

        r_q_e = self.record_queries.get("entities", {})
        if not r_q_e:
            error = {
                "error_code": 422,
                 "error_message": "no valid query"
            }

        if error:
            self.error_response.update({
                "meta": self.data_response.get("meta", {}),
                "error": error
            })
            self.data_response = self.error_response


    # -------------------------------------------------------------------------#

    def __resultSetResponse_force_granularities(self):
        prdbug(self.byc, f'authorized_granularities: {self.authorized_granularities}')
        for rs in self.data_response["response"]["result_sets"]:
            rs_granularity = self.authorized_granularities.get(rs["id"], "boolean")
            
            dbm = f'rs_granularity ({rs["id"]}): {rs_granularity}'
            prdbug(dbm, self.debug_mode)

            if not "record" in rs_granularity:
                # TODO /CUSTOM: This non-standard modification removes the results
                # but keeps the resultSets structure (handovers ...)
                rs.pop("results", None)
            if "boolean" in rs_granularity:
                rs.pop("results_count", None)
        if "boolean" in self.returned_granularity:
            self.data_response["response_summary"].pop("num_total_results", None)


    # -------------------------------------------------------------------------#

    def __response_clean_parameters(self):
        r_m = self.data_response.get("response", {})
        r_m.pop("$schema", None)


    # -------------------------------------------------------------------------#

    def __meta_clean_parameters(self):
        r_m = self.data_response.get("meta", {})

        if "beaconCollectionsResponse" in self.response_schema:
            r_m.get("received_request_summary", {}).pop("include_resultset_responses", None)


    # -------------------------------------------------------------------------#

    def __meta_add_parameters(self):

        r_m = self.data_response.get("meta", {})

        r_m.update({"info": always_merger.merge(r_m.get("info", {}), {"original_queries": self.record_queries})})

        if "test_mode" in r_m:
            r_m.update({"test_mode":self.test_mode})
        if "returned_schemas" in r_m:
            r_m.update({"returned_schemas":[self.beacon_schema]})

        info = self.entity_defaults["info"].get("content", {"api_version": "___none___"})
        for p in ["api_version", "beacon_id"]:
            if p in info.keys():
                r_m.update({p: info.get(p, "___none___")})

        form = self.form_data
        # TODO: this is hacky; need a separate setting of the returned granularity
        # since the server may decide so...
        # if self.requested_granularity and "returned_granularity" in r_m:
        #     r_m.update({"returned_granularity": form.get("requested_granularity")})

        service_meta = self.service_config.get("meta", {})
        for rrs_k, rrs_v in service_meta.items():
            r_m.update({rrs_k: rrs_v})

        if len(self.warnings) > 0:
            r_m.update({"warnings": self.warnings})

        return


    # -------------------------------------------------------------------------#

    def __meta_add_received_request_summary_parameters(self):
        r_m = self.data_response.get("meta", {})
        if not "received_request_summary" in r_m:
            return

        r_r_s = r_m["received_request_summary"]

        r_r_s.update({
            "requested_schemas": [self.beacon_schema]
        })

        for name in ["dataset_ids", "test_mode", "pagination"]:
            value = self.byc.get(name)
            if not value:
                continue
            r_r_s.update({name: value})

        vargs = self.byc.get("varguments", [])
        # TODO: a bit hacky; len == 1 woulld be the default assemblyId ...
        if len(vargs) > 1:
            r_r_s.update({"request_parameters":{"g_variant":vargs}})

        fs = self.byc.get("filters", [])
        fs_p = []
        if len(fs) > 0:
            for f in fs:
                fs_p.append(f.get("id"))
            r_r_s.update({"filters":fs_p})
        else:
            r_r_s.pop("filters", None)

        form = self.form_data
        for p in ["include_resultset_responses", "requested_granularity"]:
            if p in form and p in r_r_s:
                r_r_s.update({p: form.get(p)})

        for q in ["cohort_ids"]:
            if q in form:
                r_r_s.update({"request_parameters": always_merger.merge( r_r_s.get("request_parameters", {}), { "cohort_ids": form.get(q) })})

        info = self.entity_defaults["info"].get("content", {"api_version": "___none___"})
        for p in ["api_version"]:
            if p in info.keys():
                r_r_s.update({p: info.get(p, "___none___")})

        return


    # -------------------------------------------------------------------------#

    def __resultset_response_update_summaries(self):
        if not "beaconResultsetsResponse" in self.response_schema:
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

    def __init__(self, byc: dict):
        self.byc = byc
        self.debug_mode = byc.get("debug_mode", False)
        self.test_mode = byc.get("test_mode", False)
        self.env = byc.get("env", "server")
        self.test_mode_count = byc.get("test_mode_count", 5)
        self.dataset_ids = byc.get("dataset_ids", [])
        self.beacon_defaults = byc.get("beacon_defaults", {})
        self.entity_defaults = self.beacon_defaults.get("entity_defaults", {"info":{}})
        self.filter_definitions = byc.get("filter_definitions", {})
        self.form_data = byc.get("form_data", {})
        self.filters = byc.get("filters", [])
        self.output = byc.get("output", "___none___")
        self.response_entity_id = byc.get("response_entity_id", "filteringTerm")
        self.data_collection = byc["response_entity"].get("collection", "collations")
        self.path_id_value = byc.get("request_entity_path_id_value", False)
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
        for f in self.filters:
            ft_fs.append('(' + f.get("id", "___none___") + ')')
        if len(ft_fs) > 0:
            f_s = '|'.join(ft_fs)
            f_re = re.compile(r'^' + '|'.join(ft_fs))
        else:
            f_re = None

        # TODO: This should be derived from some entity definitions
        # TODO: whole query generation in separate function ...
        scopes = ["biosamples", "individuals", "analyses", "genomicVariations"]
        query = {}
        q_list = []

        q_scope = self.form_data.get("scope", "___none___")
        if q_scope in scopes:
            q_list.append({"scope": q_scope})

        q_types = self.form_data.get("collation_types", [])
        if len(q_types) > 0:
            q_list.append({"collation_type": {"$in": q_types }})

        if len(q_list) == 1:
            query = q_list[0]
        elif len(q_list) > 1:
            query = {"$and": q_list}

        if self.test_mode is True:
            query, error = mongo_test_mode_query(self.dataset_ids[0], f_coll, self.test_mode_count)

        for ds_id in self.dataset_ids:
            fields = {"_id": 0}
            f_s, e = mongo_result_list(ds_id, f_coll, query, fields)
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

                # TODO: this is not required & also not as defined (singular `scope`)
                # f_t.update({"scopes": scopes})
                t_f_t_s.append(f_t)
            self.filtering_terms.extend(t_f_t_s)

        self.filtering_terms_query = query

        return


    # -------------------------------------------------------------------------#

    def __return_filter_resources(self):
        r_o = {}

        f_d_s = self.filter_definitions
        collation_types = list(self.filter_collation_types)
        res_schema = object_instance_from_schema_name(self.byc, "beaconFilteringTermsResults", "definitions/Resource",
                                                      "json")
        for c_t in collation_types:
            f_d = f_d_s[c_t]
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

    def __init__(self, byc: dict):
        self.byc = byc
        self.dataset_ids = byc.get("dataset_ids", [])
        self.env = byc.get("env", "server")
        self.debug_mode = byc.get("debug_mode", False)
        self.test_mode = byc.get("test_mode", False)
        self.test_mode_count = byc.get("test_mode_count", 5)
        self.beacon_defaults = byc.get("beacon_defaults", {})
        self.entity_defaults = self.beacon_defaults.get("entity_defaults", {"info":{}})
        self.filter_definitions = byc.get("filter_definitions", {})
        self.form_data = byc.get("form_data", {})
        self.output = byc.get("output", "___none___")
        self.response_entity_id = byc.get("response_entity_id", "dataset")
        self.data_collection = byc["response_entity"].get("collection", "collations")
        self.path_id_value = byc.get("request_entity_path_id_value", False)
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
        dbstats = datasets_update_latest_stats(self.byc)
        for i, d_s in enumerate(dbstats):
            ds_id = d_s.get("id", "___none___")
            if ds_id in self.dataset_ids:
                # TODO: remove verifier hack
                for t in ["createDateTime", "updateDateTime"]:
                    d = str(d_s.get(t, "1967-11-11"))
                    if re.match(r'^\d\d\d\d\-\d\d\-\d\d$', d):
                        dbstats[i].update({t:f'{d}T00:00:00+00:00'})

        self.collections = dbstats
        self.collections_queries.update({"datasets":{}})

        return


    # -------------------------------------------------------------------------#

    def __collections_return_cohorts(self):
        if not "cohort" in self.response_entity_id:
            return

        # TODO: reshape cohorts according to schema

        cohorts =  []
        query = { "collation_type": "pgxcohort" }
        limit = 0
        c_q = self.form_data.get("cohort_ids", [])

        if len(c_q) > 0:
            query = { "id": {"$in": c_q} }
        elif self.path_id_value is not False:
            query = { "id": self.path_id_value }

        if self.test_mode is True:
            limit = self.test_mode_count

        mongo_client = MongoClient(host=environ.get("BYCON_MONGO_HOST", "localhost"))
        for ds_id in self.dataset_ids:
            mongo_db = mongo_client[ ds_id ]        
            mongo_coll = mongo_db[ "collations" ]
            for cohort in mongo_coll.find( query, limit=limit ):
                cohorts.append(cohort)

        self.collections = cohorts
        self.collections_queries.update({"cohorts":query})

        return


################################################################################

class ByconResultSets:

    def __init__(self, byc: dict):
        self.byc = byc
        self.debug_mode = byc.get("debug_mode", False)
        self.beacon_defaults = byc.get("beacon_defaults", {})
        self.env = byc.get("env", "server")
        self.entity_defaults = self.beacon_defaults.get("entity_defaults", {"info":{}})
        self.datasets_results = dict()  # the object with matched ids per dataset, per h_o
        self.datasets_data = dict()     # the object with data of requested entity per dataset
        self.result_sets = list()       # data rewrapped into the resultSets list
        self.filter_definitions = byc.get("filter_definitions", {})
        self.form_data = byc.get("form_data", {})
        self.output = byc.get("output", "___none___")
        self.data_collection = byc["response_entity"].get("collection", "biosamples")
        self.response_entity_id = byc.get("response_entity_id", "biosample")

        pagination = byc.get("pagination", {"skip": 0, "limit": 0})
        self.limit = pagination.get("limit", 0)
        self.skip = pagination.get("skip", 0)

        self.record_queries = ByconQuery(byc).recordsQuery()

        self.__create_empty_result_sets()
        self.__get_handover_access_key()
        self.__retrieve_datasets_results()


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def populatedResultSets(self):
        self.__retrieve_datasets_data()
        self.__retrieve_variants_data()
        self.__populate_result_sets()
        self.__result_sets_save_handovers()
        return self.result_sets, self.record_queries


    # -------------------------------------------------------------------------#

    def datasetsData(self):
        self.__retrieve_datasets_data()
        self.__retrieve_variants_data()
        return self.datasets_data


    # -------------------------------------------------------------------------#

    def datasetsResults(self):
        return self.datasets_results


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __get_handover_access_key(self):
        r_c = self.data_collection
        # fallback
        r_k = r_c+"_id"

        for r_t, r_d in self.entity_defaults.items():
            r_t_k = r_d.get("h->o_access_key")
            if not r_t_k:
                continue
            if r_d.get("response_entity_id", "___none___") == self.response_entity_id:
                r_k = r_d.get("h->o_access_key", r_k)

        self.handover_key = r_k

        return


    # -------------------------------------------------------------------------#

    def __result_sets_save_handovers(self):

        ho_client = MongoClient(host=environ.get("BYCON_MONGO_HOST", "localhost"))
        ho_db = ho_client[ self.byc["housekeeping_db"] ]
        ho_coll = ho_db[ self.byc["handover_coll"] ]

        for ds_id, d_s in self.datasets_results.items():
            if not d_s:
                continue
            info = {"counts": {}}
            for h_o_k, h_o in d_s.items():
                if not "target_values" in h_o:
                    continue
                h_o_size = sys.getsizeof(h_o["target_values"])
                
                dbm = f'Storage size for {ds_id}.{h_o_k}: {h_o_size / 1000000}Mb'
                prdbug(dbm, self.debug_mode)

                if h_o_size < 15000000:
                    ho_coll.update_one( { "id": h_o["id"] }, { '$set': h_o }, upsert=True )

        ho_client.close()

        return


    # -------------------------------------------------------------------------#

    def __create_empty_result_sets(self):
        r_set = object_instance_from_schema_name(self.byc, "beaconResultsets", "definitions/ResultsetInstance")
        r_sets = []
        for ds_id in self.byc.get("dataset_ids", []):
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
            ds_id = r_set["id"]
            ds_res = execute_bycon_queries(ds_id, self.record_queries, self.byc)
            self.datasets_results.update({ds_id: ds_res})            
        ds_r_duration = datetime.datetime.now() - ds_r_start
        
        dbm = f'... datasets results querying needed {ds_r_duration.total_seconds()} seconds'
        prdbug(dbm, self.debug_mode)
        return


    # -------------------------------------------------------------------------#

    def __retrieve_datasets_data(self):
        if "variants" in self.data_collection:
            return

        ds_d_start = datetime.datetime.now()
        for ds_id, ds_results in self.datasets_results.items():
            if not ds_results:
                continue
            if self.handover_key not in ds_results.keys():
                continue

            res = ds_results.get(self.handover_key, {})
            q_k = res.get("target_key", "_id")
            q_db = res.get("source_db", "___none___")
            q_coll = res.get("target_collection", "___none___")
            q_v_s = res.get("target_values", [])
            q_v_s = return_paginated_list(q_v_s, self.skip, self.limit)

            mongo_client = MongoClient(host=environ.get("BYCON_MONGO_HOST", "localhost"))
            data_coll = mongo_client[ q_db ][ q_coll ]

            r_s_res = []
            for q_v in q_v_s:
                o = data_coll.find_one({q_k: q_v })
                r_s_res.append(o)

            self.datasets_data.update({ds_id: r_s_res})
        ds_d_duration = datetime.datetime.now() - ds_d_start
        
        dbm = f'... datasets data retrieval needed {ds_d_duration.total_seconds()} seconds'
        prdbug(dbm, self.debug_mode)

        return


    # -------------------------------------------------------------------------#

    def __retrieve_variants_data(self):
        if not "variants" in self.data_collection:
            return

        ds_v_start = datetime.datetime.now()
        for ds_id, ds_results in self.datasets_results.items():

            mongo_client = MongoClient(host=environ.get("BYCON_MONGO_HOST", "localhost"))
            data_db = mongo_client[ ds_id ]
            v_coll = mongo_client[ ds_id ][ "variants" ]

            r_s_res = []

            if "variants._id" in ds_results:
                for v_id in ds_results["variants._id"]["target_values"]:
                    v = v_coll.find_one({"_id":v_id})
                    r_s_res.append(v)
                self.datasets_data.update({ds_id: r_s_res})
            # elif "variants.variant_internal_id" in ds_results:
            #     for v_id in ds_results["variants.variant_internal_id"]["target_values"]:
            #         vs = v_coll.find({"variant_internal_id":v_id})
            #         for v in vs:
            #             r_s_res.append(v)
            #     self.datasets_data.update({ds_id: r_s_res})

        ds_v_duration = datetime.datetime.now() - ds_v_start

        dbm = f'... variants retrieval needed {ds_v_duration.total_seconds()} seconds'
        prdbug(dbm, self.debug_mode)

        return


    # -------------------------------------------------------------------------#

    def __populate_result_sets(self):
        for i, r_set in enumerate(self.result_sets):
            ds_id = r_set["id"]
            ds_res = self.datasets_results.get(ds_id)
            if not ds_res:
                continue
            r_set.update({"results_handovers": dataset_response_add_handovers(ds_id, self.byc)})
            q_c = ds_res.get("target_count", 0)
            r_s_res = self.datasets_data.get(ds_id, [])
            r_s_res = reshape_resultset_results(ds_id, r_s_res, self.byc)
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

        return


################################################################################
# common response functions ####################################################
################################################################################

# def response_add_warnings(byc, message=False):
#     if message is False:
#         return
#     if len(str(message)) < 1:
#         return

#     if not "service_response" in byc:
#         return

#     if not "info" in byc["service_response"]:
#         byc["service_response"].update({"info": {}})
#     if not "warnings" in byc["service_response"]:
#         byc["service_response"]["info"].update({"warnings": []})

#     byc["service_response"]["info"]["warnings"].append(message)
