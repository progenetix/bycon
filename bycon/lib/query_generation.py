import humps, inspect, pymongo, re, sys
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

    def __init__(self, dataset_id=False):
        self.response_types = BYC.get("entity_defaults", {})
        f_t_d = self.response_types.get("filteringTerm", {})
        self.filtering_terms_coll = f_t_d.get("collection", "___none___")
        if dataset_id is False:
            self.ds_id = BYC["BYC_DATASET_IDS"][0]
        else:
            self.ds_id = dataset_id
        self.argument_definitions = BYC.get("argument_definitions", {})
        self.cytoband_definitions = BYC.get("cytobands", [])
        self.ChroNames = ChroNames()

        self.requested_entity = BYC.get("request_entity_id", False)
        self.response_entity = BYC.get("response_entity_id", "___none___")
        self.path_id_value = BYC.get("request_entity_path_id_value", [])
        prdbug(f'ByconQuery `request_entity_path_id_value`: {self.path_id_value}')
        prdbug(f'ByconQuery `response_entity_id`: {self.response_entity}')

        # TODO: call the variant type definition from inside this class since
        # e.g. multivars ... need this for each instance
        self.variant_request_type = None
        self.variant_request_definitions = BYC.get("variant_request_definitions", {})
        self.variant_type_definitions = BYC.get("variant_type_definitions", {})

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
        if len(p_id_v := self.path_id_value) < 1:
            return

        r_t_s = self.response_types
        r_e = self.requested_entity

        if not r_e:
            return
        r_c = r_t_s[r_e].get("collection")
        if not r_c:
            return

        q = {"id": {"$in":p_id_v}}

        self.queries["entities"].update({r_e: {"query":q, "collection": r_c}})
        if len(p_id_v) == 1:
            self.__id_query_add_variant_query(r_e, p_id_v)
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
        # NOTE: _all_ variants cannot be retrieved for collections
        if entity not in BYC.get("data_pipeline_entities", []):
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
        if (r_e := self.requested_entity) not in r_t_s.keys():
            return
        if not (r_c := r_t_s[r_e].get("collection")):
            return

        data_db = MongoClient(host=DB_MONGOHOST)[self.ds_id]
        if r_c not in data_db.list_collection_names():
            # TODO: warning?
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
        self.variant_multi_pars = BYC_PARS.get("variant_multi_pars", [])

        r_e = "genomicVariant"
        r_t_s = self.response_types
        r_c = r_t_s[r_e].get("collection")

        # new preprocessing which results in a list of variant queries
        self.__preprocess_variant_pars()        
        if not (v_queries := self.__loop_multivars()):
            return

        self.queries["entities"].update({r_e: {"query": v_queries, "collection": r_c}})


    # -------------------------------------------------------------------------#

    def __preprocess_variant_pars(self):
        self.variant_multi_pars = BYC_PARS.get("variant_multi_pars", [])
        v_p_s = self.variant_request_definitions.get("request_pars", [])
        v_mp_s = self.variant_request_definitions.get("multi_request_pars", [])

        # standard pars
        if (v_s_s := v_p_s & BYC_PARS.keys()):
            s_q_p_0 = {}
            for v_p in v_s_s:
                v_v = BYC_PARS.get(v_p)
                s_q_p_0.update({ v_p: v_v })
                BYC_VARGS.update({ v_p: v_v })
                prdbug(f'...__preprocess_variant_pars: {v_p} {v_v}')
            self.variant_multi_pars.append(s_q_p_0)

        for v_mp in v_mp_s:
            if len(v_mp_vs := BYC_PARS.get(v_mp, [])) > 0:
                for v in v_mp_vs:
                    self.variant_multi_pars.append({v_mp: v})

        for v_p_i, v_p_s in enumerate(self.variant_multi_pars):
            self.variant_multi_pars[v_p_i] = self.__parse_variant_parameters(v_p_s)

        # prdbug(self.variant_multi_pars)
        # exit()

    # -------------------------------------------------------------------------#


    def __parse_variant_parameters(self, variant_pars):
        v_p_s = self.variant_request_definitions.get("request_pars", [])
        a_defs = self.argument_definitions
        v_t_defs = self.variant_type_definitions

        # value checks
        v_p_c = { }

        for p_k, v_p in variant_pars.items():
            v_p = variant_pars[ p_k ]
            v_p_k = humps.decamelize(p_k)
            if "variant_type" in v_p_k:
                v_s_c = VariantTypes().variantStateChildren(v_p)
                v_p_c[ v_p_k ] = { "$in": v_s_c }
            elif "reference_name" in v_p_k:
                v_p_c[ v_p_k ] = self.ChroNames.refseq(v_p)
            else:
                v_p_c[ v_p_k ] = v_p

        return v_p_c


    # -------------------------------------------------------------------------#

    def __loop_multivars(self):

        queries = []

        for v_pars in self.variant_multi_pars:
            if not (variant_request_type := self.__get_variant_request_type(v_pars)):
                continue

            # a bit verbose for now...
            if "geneVariantRequest" in  variant_request_type:
                if (q := self.__create_geneVariantRequest_query(v_pars)):
                    queries.append(q)
                    continue
            if "cytoBandRequest" in  variant_request_type:
                if (q := self.__create_cytoBandRequest_query(v_pars)):
                    queries.append(q)
                    continue
            if "variantQueryDigestsRequest" in variant_request_type:
                if (q := self.__create_variantQueryDigestsRequest_query(v_pars)):
                    queries.append(q)
                    continue
            if "aminoacidChangeRequest" in variant_request_type:
                if (q := self.aminoacidChangeRequest(v_pars)):
                    queries.append(q)
                    continue
            if "genomicAlleleShortFormRequest" in variant_request_type:
                if (q := self.__create_genomicAlleleShortFormRequest_query(v_pars)):
                    queries.append(q)
                    continue
            if "variantBracketRequest" in variant_request_type:
                 if (q := self.__create_variantBracketRequest_query(v_pars)):
                    queries.append(q)
                    continue
            if "variantRangeRequest" in variant_request_type:
                 if (q := self.__create_variantRangeRequest_query(v_pars)):
                    queries.append(q)
                    continue
            if "variantAlleleRequest" in variant_request_type:
                if (q := self.__create_variantAlleleRequest_query(v_pars)):
                    queries.append(q)
                    continue

        return queries


    ################################################################################

    def __get_variant_request_type(self, v_pars):
        """podmd
        This method guesses the type of variant request, based on the complete
        fulfillment of the required parameters (all of `all_of`, one if `one_of`).
        In case of multiple types the one with most matched parameters is prefered.
        This may be changed to using a pre-defined request type and using this as
        completeness check only.
        TODO: Verify by schema ...
        TODO: This is all a bit too complex; probbaly better to just do it as a
              stack of dedicated tests and including a "defined to fail" query
              which is only removed after a successfull type match.
        podmd"""

        variant_request_type = None

        brts = self.variant_request_definitions.get("request_types", {})
        brts_k = brts.keys()
        prdbug(f'...brts_k: {brts_k}')
        
        # Already hard-coding some types here - if conditions are met only
        # the respective types will be evaluated since only this key is used
        if "start" in v_pars and "end" in v_pars:
            if len(v_pars[ "start" ]) == 1 and len(v_pars[ "end" ]) == 1:
                brts_k = [ "variantRangeRequest" ]
            elif len(v_pars[ "start" ]) == 2 and len(v_pars[ "end" ]) == 2:
                brts_k = [ "variantBracketRequest" ]
        elif "aminoacid_change" in v_pars:
            brts_k = [ "aminoacidChangeRequest" ]
        elif "genomic_allele_short_form" in v_pars:
            brts_k = [ "genomicAlleleShortFormRequest" ]
        elif "gene_id" in v_pars:
            brts_k = [ "geneVariantRequest" ]
        elif "cyto_bands" in  v_pars:
            brts_k = [ "cytoBandRequest" ]
        elif "variant_query_digests" in  v_pars:
            brts_k = [ "variantQueryDigestsRequest" ]
            
        vrt_matches = [ ]
        for vrt in brts_k:
            matched_par_no = 0
            needed_par_no = 0
            if "one_of" in brts[vrt]:
                needed_par_no = 1
                for one_of in brts[vrt][ "one_of" ]:
                    if one_of in v_pars:
                        matched_par_no = 1
                        continue
            if "all_of" in brts[vrt]:
                needed_par_no += len( brts[vrt][ "all_of" ] )
                for required in brts[vrt][ "all_of" ]:
                    if required in v_pars:
                        matched_par_no += 1
            if matched_par_no >= needed_par_no:
                vrt_matches.append( { "type": vrt, "par_no": matched_par_no } )
            prdbug(f'...{vrt}: {matched_par_no} of {needed_par_no}')

        if len(vrt_matches) > 0:
            vrt_matches = sorted(vrt_matches, key=lambda k: k['par_no'], reverse=True)
            variant_request_type = vrt_matches[0]["type"]

        return variant_request_type


    #--------------------------------------------------------------------------#

    def __create_geneVariantRequest_query(self, v_pars):
        # query database for gene and use coordinates to create range query
        gene_id = v_pars.get("gene_id", "___none___")
        prdbug(f'...geneVariantRequest gene_id: {gene_id}')
        gene_data = GeneInfo().returnGene(gene_id)
        prdbug(f'...geneVariantRequest gene_data: {gene_data}')
        # TODO: error report/warning
        if not gene_data:
            return False
        gene = gene_data[0]
        # Since this is a pre-processor to the range request
        v_pars = {
            "reference_name": f'refseq:{gene.get("accession_version", "___none___")}',
            "start": [ gene.get("start", 0) ],
            "end": [ gene.get("end", 1) ]
        }
        # TODO: global variant parameters by definition file
        g_p_s = ["variant_type", "variant_min_length", "variant_max_length"]
        for g_p in g_p_s:
            if g_p in BYC_VARGS:
                v_pars.update( { g_p: BYC_VARGS[g_p] } )
        q_t = self.__create_variantRangeRequest_query(v_pars)
        prdbug(f'...geneVariantRequest query result: {q_t}')

        return q_t

    #--------------------------------------------------------------------------#

    def __create_variantQueryDigestsRequest_query(self, v_pars):
        # query database for gene and use coordinates to create range query
        # http://progenetix.test/beacon/biosamples/?datasetIds=progenetix&filters=NCIT:C3058&variantQueryDigests=9:21000001-21975098--21967753-24000000:DEL,8:120000000-125000000--121000000-126000000:DUP&debugMode=
        # http://progenetix.test/services/sampleplots/?datasetIds=progenetix&filters=NCIT:C3058&variantQueryDigests=8:1-23000000--26000000-120000000:DUP,9:21000001-21975098--21967753-24000000:DEL&debugMode=
        a_d = self.argument_definitions
        vqd_pat = re.compile(a_d["variant_query_digests"]["items"]["pattern"])

        vd_s = v_pars.get("variant_query_digests", "___none___")
        if not vqd_pat.match(vd_s):
            prdbug(f'!!! no match {vd_s}')
            return False
        chro, start, end, change = vqd_pat.match(vd_s).group(1, 2, 3, 4)
        v_pars.update( {
            "reference_name": self.ChroNames.refseq(chro),
            "start": list(map(int, re.split('-', start))) 
        } )
        if end:
            v_pars.update( {
                "end": list(map(int, re.split('-', end))) 
            } )
        else:
            v_pars.pop("end", None)

        v_pars.pop("variant_query_digests", None)

        # TODO: This overrides potentially a global variant_type; so right now
        # one has to leave the type out and use a global (or none), or provide
        # a type w/ each digest
        if change:
            if ">" in change:
                ref, alt = change.split(">")
                v_pars.update( {
                    "reference_bases": ref,
                    "alternate_bases": alt
                } )
                self.variant_request_type = "variantAlleleRequest"
                q_t = self.__create_variantAlleleRequest_query(v_pars)
                return False
            else:
                v_pars.update( {
                    "variant_type": { "$in": VariantTypes().variantStateChildren(change) }
                } )

        if len(v_pars.get("start", [])) == 2:
            if len(v_pars.get("end", [])) == 2:
                self.variant_request_type = "variantBracketRequest"
                prdbug(f'...variantQueryDigestsRequest for variantBracketRequest: {v_pars}')
                return self.__create_variantBracketRequest_query(v_pars)
                prdbug(f'...variantQueryDigestsRequest -> variantBracketRequest: {q}')
        elif len(v_pars.get("start", [])) == 1:
            if len(v_pars.get("end", [])) == 1:
                self.variant_request_type = "variantRangeRequest"
                return self.__create_variantRangeRequest_query(v_pars)
        else:
            prdbug(f'!!! variantQueryDigestsRequest: {v_pars}')
            return False
        # TODO: Allele query...


    #--------------------------------------------------------------------------#

    def __create_cytoBandRequest_query(self, v_pars):
        # query database for cytoband(s) and use coordinates to create range query
        vp = v_pars
        c_b_d = self.cytoband_definitions

        if not (cb_s := vp.get("cyto_bands")):
            return False
        cbs1, chro1, start1, end1, error1 = bands_from_cytobands(cb_s)
        s_id1 = self.ChroNames.refseq(chro1)
        v_pars.update( {
            "reference_name": s_id1,
            "start": [ start1 ],
            "end": [ end1 ]
        } )
        prdbug(cb_s)
        # TODO: other global parameters (langth etc.)
        # TODO: global variant parameters by definition file
        g_p_s = ["variant_type", "variant_min_length", "variant_max_length"]
        for g_p in g_p_s:
            if g_p in BYC_VARGS:
                v_pars.update( { g_p: BYC_VARGS[g_p] } )
        self.variant_request_type = "variantRangeRequest"
        q = self.__create_variantRangeRequest_query(v_pars)
        return q


    #--------------------------------------------------------------------------#

    def __create_aminoacidChangeRequest_query(self, v_pars):    
        vp = v_pars
        if not "aminoacid_change" in vp:
            return
        v_p_defs = self.argument_definitions
        v_q = { v_p_defs["aminoacid_change"]["db_key"]: vp.get("aminoacid_change", "___none___")}

        return v_q

    #--------------------------------------------------------------------------#

    def __create_genomicAlleleShortFormRequest_query(self, v_pars):    
        vp = v_pars
        if not "genomic_allele_short_form" in vp:
            return

        v_p_defs = self.argument_definitions
        v_q = { v_p_defs["genomic_allele_short_form"]["db_key"]: vp.get("genomic_allele_short_form", "___none___")}

        return v_q

    #--------------------------------------------------------------------------#

    def __create_variantTypeRequest_query(self, v_pars):    
        v_p_defs = self.argument_definitions
        vp = v_pars
        if not "variant_type" in vp:
            return
        v_q = self.__create_in_query_for_parameter("variant_type", v_p_defs["variant_type"]["db_key"], vp)

        return v_q


    #--------------------------------------------------------------------------#

    def __create_variantRangeRequest_query(self, v_pars):    
        vp = v_pars
        v_p_defs = self.argument_definitions

        v_q = {
            v_p_defs["reference_name"]["db_key"]: vp.get("reference_name", "___none___"),
            v_p_defs["start"]["db_key"]: { "$lt": int(vp[ "end" ][-1]) },
            v_p_defs["end"]["db_key"]: { "$gt": int(vp[ "start" ][0]) }
        }

        if (l_q := self.__request_variant_size_limits(v_pars)):
            v_q.update(l_q)

        p_n = "variant_type"
        if p_n in vp:
            v_q.update( self.__create_in_query_for_parameter(p_n, v_p_defs[p_n]["db_key"], vp) )
        if "alternate_bases" in vp:
            # the N wildcard stands for any length alt bases so can be ignored
            if vp[ "alternate_bases" ] == "N":
                 v_q.update( { v_p_defs["alternate_bases"]["db_key"]: {'$regex': "." } } )
            else:
                v_q.update( { v_p_defs["alternate_bases"]["db_key"]: vp[ "alternate_bases" ] } )

        return v_q


    #--------------------------------------------------------------------------#

    def __request_variant_size_limits(self, v_pars):
        vp = v_pars
        v_p_defs = self.argument_definitions
        l_k = v_p_defs["variant_max_length"]["db_key"]
        s_q = {l_k: {}}

        p_n = "variant_min_length"
        if (minl := vp.get(p_n)):
            { v_p_defs["variant_max_length"]["db_key"]: {}}
            s_q[l_k].update( { "$gte" : minl } )
        p_n = "variant_max_length"
        if (maxl := vp.get(p_n)):
            s_q[l_k].update( { "$lte" : maxl } )

        if s_q[l_k].keys():
            return s_q

        return None
        
    #--------------------------------------------------------------------------#


    def __create_variantBracketRequest_query(self, v_pars):
        vp = v_pars
        prdbug(f'...__create_variantBracketRequest_query parameters: {vp}')
        v_p_defs = self.argument_definitions

        v_q = {
            v_p_defs["reference_name"]["db_key"]: vp["reference_name"],
            v_p_defs["start"]["db_key"]: { "$gte": sorted(vp["start"])[0], "$lt": sorted(vp["start"])[-1] },
            v_p_defs["end"]["db_key"]: { "$gte": sorted(vp["end"])[0], "$lt": sorted(vp["end"])[-1] },
            # v_p_defs["start"]["db_key"]: { "$gte": sorted(vp["start"])[0] },
            # v_p_defs["end"]["db_key"]: { "$lt": sorted(vp["end"])[-1] }
        }

        if (v_t := self.__create_in_query_for_parameter("variant_type", v_p_defs["variant_type"]["db_key"], vp)):
            v_q.update(v_t)

        return v_q


    #--------------------------------------------------------------------------#

    def __create_variantAlleleRequest_query(self, v_pars):
        """podmd
     
        podmd"""
        vp = v_pars
        v_p_defs = self.argument_definitions
        # TODO: Regexes for ref or alt with wildcard characters
        # TODO: figure out VCF vs. VRS normalization
        v_q = {
            v_p_defs["reference_name"]["db_key"]: vp["reference_name"],
            v_p_defs["start"]["db_key"]: int(vp["start"][0])
        }
        for p in [ "reference_bases", "alternate_bases" ]:
            qv = vp.get(p)
            if not qv:
                continue
            if "N" in vp[ p ]:
                qv = qv.replace("N", ".")
                v_q.update( { v_p_defs[p]["db_key"]: { '$regex': qv } } )
            else:
                v_q.update( { v_p_defs[p]["db_key"]: qv } )
            
        # v_q = { "$and": v_q_l }

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

        if len(BYC["BYC_FILTERS"]) < 1:
            return

        data_db = MongoClient(host=DB_MONGOHOST)[self.ds_id]
        coll_coll = data_db[ self.filtering_terms_coll ]
        self.collation_ids = coll_coll.distinct("id", {})

        f_lists = {}
        f_infos = {}

        for f in BYC["BYC_FILTERS"]:
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

            prdbug(f'...__query_from_filters *include_descendant_terms*: {f_desc}')

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
        f_d_s = BYC.get("filter_definitions", {})
        if f_val not in self.collation_ids:
            return False

        f_info = coll_coll.find_one({"id": f_val})
        f_ct = f_info.get("collation_type", "___none__")
        if not (f_d := f_d_s.get(f_ct)):
            return False

        # TODO: the whole "get entity" is a bit cumbersome ... should be added
        # to each collation in the next generation round
        f_info.update({"entity": f_d.get("entity", "biosample")})

        return f_info


    # -------------------------------------------------------------------------#

    def __query_from_filter_definitions(self, f_val):
        f_d_s = BYC.get("filter_definitions", {})
        f_info = {
            "id": f_val,
            "scope": "biosamples",
            "type": "___undefined___",
            "db_key": "___undefined___",
            "child_terms": [f_val]
        }

        for f_d in f_d_s.values():
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
        geo_q, geo_pars = geo_query()
        if not geo_q:
            return
        self.__update_queries_for_entity(geo_q, entity)


    # -------------------------------------------------------------------------#

    def __query_from_hoid(self):
        """
        This non-standard (_i.e._ not Beacon spec'd) type of query generation retrieves
        the query parameters and values from a handover object, _i.e._ the stored results
        of a previous query.
        These query values can be combined with additional parameters.
        """
        if not (accessid := BYC_PARS.get("accessid")):
            return

        ho_client = MongoClient(host=DB_MONGOHOST)
        ho_coll = ho_client[HOUSEKEEPING_DB][HOUSEKEEPING_HO_COLL]
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

def geo_query():
    g_l_d = BYC.get("geoloc_definitions", {})
    g_p_defs = g_l_d.get("parameters", {})
    g_p_rts = g_l_d.get("request_types", {})
    geo_root = g_l_d.get("geo_root", "___none___")

    geo_q = None
    geo_pars = None
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

