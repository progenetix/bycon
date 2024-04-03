import inspect, pymongo, re, sys
from bson import SON
from os import environ
from pymongo import MongoClient

from bycon_helpers import days_from_iso8601duration, prdbug, return_paginated_list
from config import *
from cytoband_parsing import bands_from_cytobands
from genome_utils import ChroNames, GeneInfo, VariantTypes

################################################################################

class ByconQuery():
    """
    Bycon queries are collected as an object with per data collection query objects,
    ready to be run against the respective entity databases.
    The definition against per-collection in contrast to per-entity is due to the
    incongruency of collection use, e.g. the utilization of the "analyses" collection
    for both "analysis" and "run" entities.

    Query object:

    ```
    entity_queries:
        __entity__:
            query: { __query__ }
            collection: __collection__
        ...

    expand: True/False                          | Flag to terminate collection
                                                | of further query items, e.g.
                                                | after creating an id query

    variant_id_query: { __variant_id_query__ }  | special query added to queries
                                                | by id values, e.g.
                                                | * `/biosamples/{id}
                                                | * `?biosampleIds={id1,id2,...}
                                                | ... to retrieve all variants for
                                                | the matched samples, individuals
                                                | etc.
    ```
    """

    def __init__(self, byc: dict, dataset_id=False):
        self.response_types = BYC.get("entity_defaults", {})
        f_t_d = self.response_types.get("filteringTerm", {})
        self.filtering_terms_coll = f_t_d.get("collection", "___none___")
        if dataset_id is False:
            self.ds_id = byc.get("dataset_ids", False)[0]
        else:
            self.ds_id = dataset_id
        self.argument_definitions = byc.get("argument_definitions", {})
        self.cytoband_definitions = byc.get("cytobands", [])
        self.ChroNames = ChroNames()
        self.filters = byc.get("filters", [])

        self.requested_entity = byc.get("request_entity_id", False)
        self.response_entity = byc.get("response_entity_id", "___none___")
        self.path_id_value = byc.get("request_entity_path_id_value", False)

        self.variant_request_type = byc.get("variant_request_type", "___none___")
        self.variant_request_definitions = byc.get("variant_request_definitions", {})
        self.VariantTypes = VariantTypes(byc.get("variant_type_definitions", {}))
        self.varguments = byc.get("varguments", {})

        self.filter_definitions = byc.get("filter_definitions", {})
        self.geoloc_definitions = byc.get("geoloc_definitions", {})

        self.limit = BYC_PARS.get("limit")
        self.skip = BYC_PARS.get("skip")

        self.queries = {
            "expand": True,
            "entities": {}
        }

        self.__queries_for_test_mode()
        self.__query_from_path_id()
        self.__update_queries_from_id_values()
        self.__query_from_hoid()
        self.__query_from_variant_pars()
        self.__query_from_filters()
        self.__query_from_geoquery()


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def recordsQuery(self):
        return self.queries


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __query_from_path_id(self):
        if self.queries.get("expand") is False:
            return
        p_id_v = self.path_id_value
        if not p_id_v:
            return

        r_t_s = self.response_types
        r_e = self.requested_entity
        if not r_e:
            return
        r_c = r_t_s[r_e].get("collection")
        if not r_c:
            return

        q = {"id": p_id_v}

        self.queries["entities"].update({r_e: {"query":q, "collection": r_c}})
        self.__id_query_add_variant_query(r_e, [p_id_v])
        self.queries.update({"expand": False})


    # -------------------------------------------------------------------------#

    def __update_queries_from_id_values(self):
        if self.queries.get("expand") is False:
            return
        argdefs = self.argument_definitions
        for p_k, id_v_s in BYC_PARS.items():
            if not p_k.endswith("_ids"):
                continue
            if not (entity := argdefs[p_k].get("byc_entity")):
                continue
            q = False
            if len(id_v_s) < 1:
                continue
            elif len(id_v_s) == 1:
                q = {"id": id_v_s[0]}
                self.__id_query_add_variant_query(entity, id_v_s)
            elif len(id_v_s) > 1:
                q = {"id": {"$in": id_v_s}}
                self.__id_query_add_variant_query(entity, id_v_s)

            if q is not False:
                self.__update_queries_for_entity(q, entity)
                self.queries.update({"expand": False})


    # -------------------------------------------------------------------------#

    def __id_query_add_variant_query(self, entity, entity_ids):

        if entity not in ("biosample", "individual", "analysis", "run"):
            return

        v_q_id = f'{entity}_id'
        v_q_id = re.sub("analysis", "callset", v_q_id)
        v_q_id = re.sub("run", "callset", v_q_id)

        if len(entity_ids) == 1:
            q = {v_q_id: entity_ids[0]}
        elif len(entity_ids) > 1:
            q = {v_q_id: {"$in": entity_ids } }
        else:
            return

        self.queries.update({"variant_id_query": q})


    # -------------------------------------------------------------------------#

    def __queries_for_test_mode(self):
        if BYC["TEST_MODE"] is False:
            return
        if self.queries.get("expand") is False:
            return

        ret_no = BYC_PARS.get("test_mode_count", 5)
        r_t_s = self.response_types
        if (r_e := self.response_entity) not in r_t_s.keys():
            return
        if not (r_c := r_t_s[r_e].get("collection")):
            return

        data_db = MongoClient(host=DB_MONGOHOST)[self.ds_id]
        data_collnames = data_db.list_collection_names()

        if r_c not in data_collnames:
            return

        data_coll = data_db[r_c]
        rs = list(data_coll.aggregate([{"$sample": {"size": ret_no}}]))

        q = {"_id": {"$in": list(s["_id"] for s in rs)}}

        self.queries["entities"].update({r_e: {"query": q, "collection": r_c}})
        self.queries.update({"expand": False})


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __query_from_variant_pars(self):
        if self.queries.get("expand") is False:
            return
        if not self.variant_request_type:
            return
        if self.variant_request_type not in self.variant_request_definitions.get("request_types", {}).keys():
            return

        r_e = "genomicVariant"
        r_t_s = self.response_types
        r_c = r_t_s[r_e].get("collection")

        q = False

        # if "variantTypeRequest" in self.variant_request_type and len(self.filters) > 0:
        #     q = self.__create_variantTypeRequest_query()

        if "geneVariantRequest" in  self.variant_request_type:
            q = self.__create_geneVariantRequest_query()
        elif "cytoBandRequest" in  self.variant_request_type:
            q = self.__create_cytoBandRequest_query()
        elif "variantQueryDigestsRequest" in  self.variant_request_type:
            q = self.__create_variantQueryDigestsRequest_query()
        elif "aminoacidChangeRequest" in self.variant_request_type:
            q = self.__create_aminoacidChangeRequest_query()
        elif "genomicAlleleShortFormRequest" in self.variant_request_type:
            q = self.__create_genomicAlleleShortFormRequest_query()
        elif "variantBracketRequest" in self.variant_request_type:
            q = self.__create_variantBracketRequest_query()
        elif "variantRangeRequest" in self.variant_request_type:
            q = self.__create_variantRangeRequest_query()
        elif "variantAlleleRequest" in self.variant_request_type:
            q = self.__create_variantAlleleRequest_query()


        if q is False:
            return

        self.queries["entities"].update({r_e: {"query": q, "collection": r_c}})
        prdbug(self.queries)


    #--------------------------------------------------------------------------#

    def __create_geneVariantRequest_query(self):
        # query database for gene and use coordinates to create range query
        vp = self.varguments
        q = []
        for g in vp["gene_id"]:
            gene_data = GeneInfo().returnGene(g)
            # TODO: error report/warning
            if not gene_data:
                continue
            gene = gene_data[0]
            # Since this is a pre-processor to the range request
            self.varguments.update( {
                "reference_name": f'refseq:{gene.get("accession_version", "___none___")}',
                "start": [ gene.get("start", 0) ],
                "end": [ gene.get("end", 1) ]
            } )
            self.variant_request_type = "variantRangeRequest"
            q_t = self.__create_variantRangeRequest_query()
            q.append(q_t)

        return q

    #--------------------------------------------------------------------------#

    def __create_variantQueryDigestsRequest_query(self):
        # query database for gene and use coordinates to create range query
        # http://progenetix.test/beacon/biosamples/?datasetIds=progenetix&filters=NCIT:C3058&variantQueryDigests=9:21000001-21975098--21967753-24000000:DEL,8:120000000-125000000--121000000-126000000:DUP&debugMode=
        # http://progenetix.test/services/sampleplots/?datasetIds=progenetix&filters=NCIT:C3058&variantQueryDigests=8:1-23000000--26000000-120000000:DUP,9:21000001-21975098--21967753-24000000:DEL&debugMode=
        vp = self.varguments
        a_d = self.argument_definitions
        vqd_pat = re.compile(a_d["variant_query_digests"]["items"]["pattern"])

        vd_s = vp.get("variant_query_digests", [])
        q = []
        for qd in vd_s:
            if not vqd_pat.match(qd):
                prdbug(f'!!! no match {qd}')
                continue
            chro, start, end, change = vqd_pat.match(qd).group(1, 2, 3, 4)
            self.varguments.update( {
                "reference_name": self.ChroNames.refseq(chro),
                "start": list(map(int, re.split('-', start))),
                "end": list(map(int, re.split('-', end)))
            } )
            # TODO: This overrides potentially a global variant_type; so right now
            # one has to leave the type out and use a global (or none), or provide
            # a type w/ each digest
            if change:
                self.varguments.update( {
                    "variant_type": { "$in": self.VariantTypes.variantStateChildren(change) }
                } )

            if len(self.varguments.get("start", [])) == 2:
                if len(self.varguments.get("end", [])) == 2:
                    self.variant_request_type = "variantBracketRequest"
                    q_t = self.__create_variantBracketRequest_query()
                    q.append(q_t)
            elif len(self.varguments.get("start", [])) == 1:
                if len(self.varguments.get("end", [])) == 1:
                    self.variant_request_type = "variantRangeRequest"
                    q_t = self.__create_variantRangeRequest_query()
                    q.append(q_t)

        return q


    #--------------------------------------------------------------------------#

    def __create_cytoBandRequest_query(self):
        # query database for cytoband(s) and use coordinates to create range query
        vp = self.varguments
        a_d = self.argument_definitions
        c_b_d = self.cytoband_definitions

        cb_s = vp.get("cyto_bands", [])
        cbs1, chro1, start1, end1, error1 = bands_from_cytobands(cb_s[0], c_b_d, a_d)
        s_id1 = self.ChroNames.refseq(chro1)
        self.varguments.update( {
            "reference_name": s_id1,
            "start": [ start1 ],
            "end": [ end1 ]
        } )
        if len(cb_s) == 1:           
            self.variant_request_type = "variantRangeRequest"
            q = self.__create_variantRangeRequest_query()
            return q

        elif len(cb_s) > 1:
            cbs2, chro2, start2, end2, error2 = bands_from_cytobands(cb_s[1], c_b_d, a_d)
            s_id2 = self.ChroNames.refseq(chro2)

            # TODO: here is a prototype for a variant query list, used for co-occurring
            # variants in the same biosample
            if s_id1 != s_id2:
                v_q_l = []
                q1 = self.__create_variantRangeRequest_query()
                v_q_l.append(q1)
                self.varguments.update( {
                    "reference_name": s_id2,
                    "start": [ start2 ],
                    "end": [ end2 ]
                } )
                q2 = self.__create_variantRangeRequest_query()
                v_q_l.append(q2)
                self.variant_request_type = "variantsMultimatchRequest"
                return v_q_l

            self.varguments.update( {
                "start": [ start1, start2 ],
                "end": [ end1, end2 ]
            } )
            self.variant_request_type = "variantBracketRequest"
            q = self.__create_variantBracketRequest_query()
            return q


    #--------------------------------------------------------------------------#

    def __create_aminoacidChangeRequest_query(self):    
        vp = self.varguments
        if not "aminoacid_change" in vp:
            return
        v_p_defs = self.argument_definitions
        v_q = { v_p_defs["aminoacid_change"]["db_key"]: vp.get("aminoacid_change", "___none___")}

        return v_q

    #--------------------------------------------------------------------------#

    def __create_genomicAlleleShortFormRequest_query(self):    
        vp = self.varguments
        if not "genomic_allele_short_form" in vp:
            return

        v_p_defs = self.argument_definitions
        v_q = { v_p_defs["genomic_allele_short_form"]["db_key"]: vp.get("genomic_allele_short_form", "___none___")}

        return v_q

    #--------------------------------------------------------------------------#

    def __create_variantTypeRequest_query(self):    
        v_p_defs = self.argument_definitions
        vp = self.varguments
        if not "variant_type" in vp:
            return
        v_q = self.__create_in_query_for_parameter("variant_type", v_p_defs["variant_type"]["db_key"], vp)

        return v_q


    #--------------------------------------------------------------------------#

    def __create_variantRangeRequest_query(self):    
        vp = self.varguments
        v_p_defs = self.argument_definitions

        v_q_l = [
            { v_p_defs["reference_name"]["db_key"]: vp.get("reference_name", "___none___")},
            { v_p_defs["start"]["db_key"]: { "$lt": int(vp[ "end" ][-1]) } },
            { v_p_defs["end"]["db_key"]: { "$gt": int(vp[ "start" ][0]) } }
        ]

        p_n = "variant_min_length"
        if p_n in vp:
            v_q_l.append( { v_p_defs[p_n]["db_key"]: { "$gte" : vp[p_n] } } )
        p_n = "variant_max_length"
        if "variant_max_length" in vp:
            v_q_l.append( { v_p_defs[p_n]["db_key"]: { "$lte" : vp[p_n] } } )

        p_n = "variant_type"
        if p_n in vp:
            v_q_l.append( self.__create_in_query_for_parameter(p_n, v_p_defs[p_n]["db_key"], vp) )
        elif "alternate_bases" in vp:
            # the N wildcard stands for any length alt bases so can be ignored
            if vp[ "alternate_bases" ] == "N":
                 v_q_l.append( { v_p_defs["alternate_bases"]["db_key"]: {'$regex': "." } } )
            else:
                v_q_l.append( { v_p_defs["alternate_bases"]["db_key"]: vp[ "alternate_bases" ] } )

        v_q = { "$and": v_q_l }

        return v_q


    #--------------------------------------------------------------------------#

    def __create_variantBracketRequest_query(self):
        vp = self.varguments
        v_p_defs = self.argument_definitions

        v_q = { "$and": [
            { v_p_defs["reference_name"]["db_key"]: vp["reference_name"] },
            { v_p_defs["start"]["db_key"]: { "$lt": sorted(vp["start"])[-1] } },
            { v_p_defs["end"]["db_key"]: { "$gte": sorted(vp["end"])[0] } },
            { v_p_defs["start"]["db_key"]: { "$gte": sorted(vp["start"])[0] } },
            { v_p_defs["end"]["db_key"]: { "$lt": sorted(vp["end"])[-1] } },
            self.__create_in_query_for_parameter("variant_type", v_p_defs["variant_type"]["db_key"], vp)
        ]}

        return v_q


    #--------------------------------------------------------------------------#

    def __create_variantAlleleRequest_query(self):
        """podmd
     
        podmd"""
        vp = self.varguments
        v_p_defs = self.argument_definitions
        # TODO: Regexes for ref or alt with wildcard characters

        v_q_l = [
            { v_p_defs["reference_name"]["db_key"]: vp["reference_name"] },
            { v_p_defs["start"]["db_key"]: int(vp["start"][0]) }
        ]
        for p in [ "reference_bases", "alternate_bases" ]:
            if not vp[ p ] == "N":
                if "N" in vp[ p ]:
                    rb = vp[ p ].replace("N", ".")
                    v_q_l.append( { v_p_defs[p]["db_key"]: { '$regex': rb } } )
                else:
                     v_q_l.append( { v_p_defs[p]["db_key"]: vp[ p ] } )
            
        v_q = { "$and": v_q_l }

        return v_q


    #--------------------------------------------------------------------------#

    def __create_in_query_for_parameter(self, par, qpar, q_pars):

        if not isinstance(q_pars[par], list):
            return {qpar: q_pars[par]}
        try:
            q_pars[par][0]
        except IndexError:
            return {}
     
        if len(q_pars[ par ]) > 1:
            return {qpar: {"$in": q_pars[par]}}

        return {qpar: q_pars[par][0]}


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __query_from_filters(self):
        if self.queries.get("expand") is False:
            return

        if len(self.filters) < 1:
            return

        data_db = MongoClient(host=DB_MONGOHOST)[self.ds_id]
        coll_coll = data_db[ self.filtering_terms_coll ]
        self.collation_ids = coll_coll.distinct("id", {})

        f_lists = {}
        f_infos = {}

        for f in self.filters:
            f_val = f["id"]
            f_neg = f.get("excluded", False)
            if re.compile(r'^!').match(f_val):
                f_neg = True
                f_val = re.sub(r'^!', '', f_val)
            f_val = re.sub(r'^!', '', f_val)
            f_desc = f.get("includeDescendantTerms", BYC_PARS.get("include_descendant_terms"))

            f_info = self.__query_from_collationed_filter(coll_coll, f_val)
            if f_info is False:
                f_info = self.__query_from_filter_definitions(f_val)

            if f_info is False:
                continue

            if f_neg is True:
                f_info.update({"is_negated": True})

            f_entity = f_info.get("entity")
            if f_entity not in f_lists.keys():
                f_lists.update({f_entity: {}})
            if f_entity not in f_infos.keys():
                f_infos.update({f_entity: {}})

            f_field = f_info.get("db_key", "id")
            if f_field not in f_lists[f_entity].keys():
                f_lists[f_entity].update({f_field: []})
            if f_field not in f_infos[f_entity].keys():
                f_infos[f_entity].update({f_field: f_info})

            # TODO: needs a general solution; so far for the iso age w/
            #       pre-calculated days field...
            if "alphanumeric" in f_info.get("type", "ontology"):
                f_class, comp, val = re.match(r'^(\w+):([<>=]+?)(\w[\w.]+?)$', f_info["id"]).group(1, 2, 3)
                if "iso8601duration" in f_info.get("format", "___none___"):
                    val = days_from_iso8601duration(val)
                f_lists[f_entity][f_field].append(self.__mongo_comparator_query(comp, val))
            elif f_desc is True:
                if f_neg is True:
                    f_lists[f_entity][f_field].append({'$nin': f_info["child_terms"]})
                else:
                    f_lists[f_entity][f_field].extend(f_info["child_terms"])
            else:
                if f_neg is True:
                    f_lists[f_entity][f_field].append({'$nin': [f_info["id"]]})
                else:
                    f_lists[f_entity][f_field].append(f_info["id"])

        # now processing the filter lists into the queries
        for f_entity in f_lists.keys():
            f_s_l = []
            for f_field, f_query_vals in f_lists[f_entity].items():
                if len(f_query_vals) == 1:
                    f_s_l.append({f_field: f_query_vals[0]})
                else:
                    if "alphanumeric" in f_infos[f_entity][f_field].get("type", "ontology"):
                        q_l = []
                        for a_q_v in f_query_vals:
                            q_l.append({f_field: a_q_v})
                        f_s_l.append({"$and": q_l})
                    else:
                        f_s_l.append({f_field: {"$in": f_query_vals}})

            for q in f_s_l:
                self.__update_queries_for_entity(q, f_entity)


    # -------------------------------------------------------------------------#

    def __query_from_collationed_filter(self, coll_coll, f_val):
        f_d_s = self.filter_definitions
        if f_val not in self.collation_ids:
            return False

        f_info = coll_coll.find_one({"id": f_val})
        f_ct = f_info.get("collation_type", "___none__")
        f_d = f_d_s.get(f_ct)
        if not f_d:
            return False

        # TODO: the whole "get entity" is a bit cumbersome ... should be added
        # to each collation in the next generation round
        f_info.update({"entity": f_d.get("entity", "biosample")})

        return f_info


    # -------------------------------------------------------------------------#

    def __query_from_filter_definitions(self, f_val):
        f_defs = self.filter_definitions
        f_info = {
            "id": f_val,
            "scope": "biosamples",
            "type": "___undefined___",
            "db_key": "___undefined___",
            "child_terms": [f_val]
        }

        for f_d in f_defs.values():
            f_re = re.compile(f_d.get("pattern", "___none___"))
            if f_re.match(f_val):
                f_info = {
                    "id": f_val,
                    "scope": f_d.get("scope", "biosamples"),
                    "entity": f_d.get("entity", "biosample"),
                    "db_key": f_d["db_key"],
                    "type": f_d.get("type", "ontology"),
                    "format": f_d.get("format", "___none___"),
                    "child_terms": [f_val]
                }
                return f_info

        return False


    # -------------------------------------------------------------------------#

    def __query_from_geoquery(self, entity="biosample"):
        geo_q, geo_pars = geo_query(self.geoloc_definitions)
        if not geo_q:
            return
        self.__update_queries_for_entity(geo_q, entity)


    # -------------------------------------------------------------------------#

    def __query_from_hoid(self):
        """
        This non-standard (_i.e._ not Beacon spec'd) type of query generation retrieves
        the query paramters and values from a handover object, _i.e._ the stored results
        of a previous query.
        These query values can be combined with additional parameters.
        """
        if not (accessid := BYC_PARS.get("accessid")):
            return

        ho_client = MongoClient(host=DB_MONGOHOST)
        ho_coll = ho_client[HOUSEKEEPING_DB].ho_db[HOUSEKEEPING_HO_COLL]
        h_o = ho_coll.find_one({"id": accessid})

        # accessid overrides ... ?
        if not h_o:
            return

        t_k = h_o["target_key"]
        t_v = h_o["target_values"]
        c_n = h_o["target_collection"]
        t_e = h_o["target_entity"]
        t_c = h_o["target_count"]

        t_v = return_paginated_list(t_v, self.skip, self.limit)
        if len(t_v) < 1:
            return
        h_o_q = {t_k: {'$in': t_v}}
        self.__update_queries_for_entity(h_o_q, t_e)


    # -------------------------------------------------------------------------#

    def __update_queries_for_entity(self, query, entity):
        logic = self.__boolean_to_mongo_logic(BYC_PARS.get("filter_logic"))
        r_t_s = self.response_types
        r_c = r_t_s[entity].get("collection")
        q_e = self.queries.get("entities")

        if entity not in q_e:
            q_e.update({entity:{"query": query, "collection": r_c}})
        elif logic in q_e[entity]["query"]:
            q_e[entity]["query"][logic].append(query)
        else:
            q_e[entity].update({"query": {logic: [q_e[entity]["query"], query]}})
        self.queries.update({"entities": q_e})


    # -------------------------------------------------------------------------#

    def __boolean_to_mongo_logic(self, logic: str = "AND") -> str:
        if "OR" in logic.upper():
            return '$or'
        return '$and'


    # -------------------------------------------------------------------------#

    def __mongo_comparator_query(self, comparator, value):
        mongo_comps = {
            ">": '$gt',
            ">=": '$gte',
            "<": '$lt',
            "<=": '$lte',
            "=": '$eq'
        }
        c = mongo_comps.get(comparator, '$eq')
        return {c: value}


################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
################################################################################

# TODO: GeoQuery class

def geo_query(geoloc_definitions):
    geo_q = None
    geo_pars = None
    g_p_defs = geoloc_definitions["parameters"]
    g_p_rts = geoloc_definitions["request_types"]
    geo_root = geoloc_definitions["geo_root"]
    geo_form_pars = {}
    for g_f_p in g_p_defs.keys():
        f_v = BYC_PARS.get(g_f_p)
        if f_v:
            geo_form_pars.update({g_f_p: f_v})
    if len(geo_form_pars.keys()) < 1:
        return geo_q, geo_pars
    req_type = ""
    # TODO: Make this modular & fix the one_of interpretation to really only 1
    for rt in g_p_rts:
        g_p = {}
        min_p_no = 1
        mat_p_no = 0
        if "all_of" in g_p_rts[rt]:
            g_q_k = g_p_rts[rt]["all_of"]
            min_p_no = len(g_q_k)
        elif "one_of" in g_p_rts[rt]:
            g_q_k = g_p_rts[rt]["one_of"]
        else:
            continue

        all_p = g_p_rts[rt].get("any_of", []) + g_q_k
        for g_k in g_p_defs.keys():
            if g_k not in all_p:
                continue
            g_default = g_p_defs[g_k].get("default")
            # TODO: This is an ISO lower hack ...
            if g_k in geo_form_pars.keys():
                g_v = geo_form_pars[g_k]
            elif g_default:
                g_v = g_default
            else:
                continue
            if not re.compile(g_p_defs[g_k]["pattern"]).match(str(g_v)):
                continue
            if "float" in g_p_defs[g_k]["type"]:
                g_p[g_k] = float(g_v)
            else:
                g_p[g_k] = g_v
            if g_k in g_q_k:
                mat_p_no += 1

        if mat_p_no < min_p_no:
            continue

        req_type = rt
        geo_pars = g_p

    if "city" in req_type:
        geo_q = return_geo_city_query(geo_root, geo_pars)
        return geo_q, geo_pars

    if "id" in req_type:
        geo_q = {"id": re.compile(geo_pars["id"], re.IGNORECASE)}
        return geo_q, geo_pars
    if "ISO3166alpha2" in req_type:
        geo_q = {"provenance.geo_location.properties.ISO3166alpha2": BYC_PARS["iso3166alpha2"].upper()}
        return geo_q, geo_pars
    if "geoquery" in req_type:
        geoq_l = [return_geo_longlat_query(geo_root, geo_pars)]
        for g_k in g_p_rts["geoquery"]["any_of"]:
            if g_k in geo_pars.keys():
                g_v = geo_pars[g_k]
                geopar = ".".join([geo_root, "properties", g_k])
                geoq_l.append({geopar: re.compile(r'^' + str(g_v), re.IGNORECASE)})

        if len(geoq_l) > 1:
            geo_q = {"$and": geoq_l}
        else:
            geo_q = geoq_l[0]
    return geo_q, geo_pars


################################################################################

def return_geo_city_query(geo_root, geo_pars):
    geoq_l = []

    for g_k, g_v in geo_pars.items():
        if len(geo_root) > 0:
            geopar = ".".join([geo_root, "properties", g_k])
        else:
            geopar = ".".join(["properties", g_k])

        geoq_l.append({geopar: re.compile(r'^' + str(g_v), re.IGNORECASE)})

    if len(geoq_l) > 1:
        return {"$and": geoq_l}
    else:
        return geoq_l[0]


################################################################################

def return_geo_longlat_query(geo_root, geo_pars):
    if len(geo_root) > 0:
        geojsonpar = ".".join((geo_root, "geometry"))
    else:
        geojsonpar = "geo_location.geometry"

    geo_q = {
        geojsonpar: {
            '$near': SON(
                [
                    (
                        '$geometry', SON(
                            [
                                ('type', 'Point'),
                                ('coordinates', [
                                    geo_pars["geo_longitude"],
                                    geo_pars["geo_latitude"]
                                ])
                            ]
                        )
                    ),
                    ('$maxDistance', geo_pars["geo_distance"])
                ]
            )
        }
    }

    return geo_q


################################################################################

