import humps, inspect, pymongo, re, sys
from bson import SON
from os import environ
from pymongo import MongoClient

from bycon_helpers import days_from_iso8601duration, mongo_and_or_query_from_list, prdbug, prjsonnice, return_paginated_list
from config import *
from genome_utils import ChroNames, Cytobands, GeneInfo, VariantTypes
from parameter_parsing import ByconFilters

################################################################################
################################################################################
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
        self.argument_definitions = BYC["argument_definitions"].get("$defs", {})
        self.cytoband_definitions = BYC.get("cytobands", [])
        self.ChroNames = ChroNames()

        self.requested_entity = BYC.get("request_entity_id", False)
        self.response_entity = BYC.get("response_entity", {})
        self.response_entity_id = BYC.get("response_entity_id", "")

        # TODO: call the variant type definition from inside this class since
        # e.g. multivars ... need this for each instance
        self.variant_request_type = None
        self.variant_request_definitions = BYC.get("variant_request_definitions", {})
        self.variant_par_names = self.variant_request_definitions.get("request_pars", [])
        self.variant_par_names += self.variant_request_definitions.get("VQS_pars", [])

        self.variant_type_definitions = BYC.get("variant_type_definitions", {})

        self.limit = BYC_PARS.get("limit")
        self.skip = BYC_PARS.get("skip")
        self.filters = ByconFilters().get_filters()

        self.queries = {
            "expand": True,
            "entities": {}
        }

        self.__queries_for_test_mode()
        self.__update_queries_from_id_values()
        self.__query_from_hoid()
        self.__query_from_variant_pars()
        self.__query_from_filters()
        self.__query_from_geoquery()


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def recordsQuery(self):
        prdbug(f'...recordsQuery: {self.queries}')
        return self.queries


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
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
                q = [{"id": id_v_s[0]}]
                self.__id_query_add_variant_query(entity, id_v_s)
            elif len(id_v_s) > 1:
                q = [{"id": {"$in": id_v_s}}]
                self.__id_query_add_variant_query(entity, id_v_s)

            if q is not False:
                self.__update_queries_for_entity(q, entity)
                self.queries.update({"expand": False})


    # -------------------------------------------------------------------------#

    def __id_query_add_variant_query(self, entity, entity_ids):
        # NOTE: _all_ variants cannot be retrieved for collections
        if "variant" in entity.lower():
            return

        v_q_id = f'{entity}_id'
        v_q_id = re.sub("run", "analysis", v_q_id)

        if len(entity_ids) == 1:
            q = [{v_q_id: entity_ids[0]}]
        elif len(entity_ids) > 1:
            q = [{v_q_id: {"$in": entity_ids } }]
        else:
            return

        BYC.update({"AGGREGATE_VARIANT_RESULTS": False})

        self.queries["entities"].update({
            "genomicVariant": {
                "query": q,
                "collection": "variants"
            }
        })


    # -------------------------------------------------------------------------#

    def __queries_for_test_mode(self):
        if BYC["TEST_MODE"] is False:
            return
        if self.queries.get("expand") is False:
            return

        ret_no = BYC_PARS.get("test_mode_count", 5)
        if not (r_c := self.response_entity.get("collection")):
            return

        data_db = MongoClient(host=DB_MONGOHOST)[self.ds_id]
        if r_c not in data_db.list_collection_names():
            # TODO: warning?
            return

        data_coll = data_db[r_c]
        rs = list(data_coll.aggregate([{"$sample": {"size": ret_no}}]))

        q = [{"id": {"$in": list(s["id"] for s in rs)}}]

        self.queries["entities"].update({self.response_entity_id: {"query": q, "collection": r_c}})
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
        v_m_ps = BYC_PARS.get("variant_multi_pars", [])

        v_p_s = self.variant_par_names
        # standard pars
        s_q_p_0 = {}
        if (v_s_s := v_p_s & BYC_PARS.keys()):
            for v_p in v_s_s:
                s_q_p_0.update({ v_p: BYC_PARS.get(v_p) })
        if len(s_q_p_0.keys()) > 0:
            v_m_ps.append(s_q_p_0)

        vips = []
        for v in v_m_ps:
            vp = {}

            if (v_s_s := v_p_s & v.keys()):
                for v_p in v_s_s:
                    vp.update({ v_p: v.get(v_p) })
                if len(vp.keys()) > 0:
                    vips.append(self.__parse_variant_parameters(vp))

        self.variant_multi_pars = vips


    # -------------------------------------------------------------------------#

    def __parse_variant_parameters(self, variant_pars):
        v_p_s = self.variant_par_names
        a_defs = self.argument_definitions
        v_t_defs = self.variant_type_definitions

        # value checks
        v_p_c = { }
        pop_list = []
        for p_k, v_p in variant_pars.items():
            v_p_k = humps.decamelize(p_k)
            if "variant_type" in v_p_k:
                v_s_c = VariantTypes().variantStateChildren(v_p)
                v_p_c.update({v_p_k: { "$in": v_s_c }})
                continue
            if "reference_name" in v_p_k or "mate_name" in v_p_k:
                v_p_c.update({v_p_k: self.ChroNames.refseq(v_p)})
                continue


            # VQS - TODO (remapping to be transferred ...)
            if "reference_accession" in v_p_k:
                v_p_c.update({"reference_name": self.ChroNames.refseq(v_p)})
                pop_list.append(p_k)
                continue
            if "adjacency_accession" in v_p_k:
                v_p_c.update({"mate_name": self.ChroNames.refseq(v_p)})
                pop_list.append(p_k)
                continue
            if "breakpoint_range" in v_p_k:
                if len(v_p) == 1:
                    v_p.append(v_p[0] + 1)
                v_p_c.update({"start": [v_p[0]], "end": [v_p[1]]})
                pop_list.append(p_k)
                continue
            if "adjacency_range" in v_p_k:
                if len(v_p) == 1:
                    v_p.append(v_p[0] + 1)
                v_p_c.update({"mate_start": [v_p[0]], "mate_end": [v_p[1]]})
                pop_list.append(p_k)
                continue
            # VQS 
            if "copy_change" in v_p_k:
                v_s_c = VariantTypes().variantStateChildren(v_p)
                v_p_c.update({"variant_type": { "$in": v_s_c }})
                pop_list.append(p_k)
                continue               
            # VQS
            if "sequence_length" in v_p_k:
                if len(v_p) == 1:
                    v_p.append(v_p[0] + 1)
                v_p_c.update({
                    "variant_min_length": v_p[0],
                    "variant_max_length": v_p[1]
                })
                pop_list.append(p_k)
                continue
            
            v_p_c.update({v_p_k: v_p})

        for p_l in pop_list:
            variant_pars.pop(p_l, None)

        return v_p_c


    # -------------------------------------------------------------------------#

    def __loop_multivars(self):

        # TODO: proper self.queries handling

        queries = []

        for v_pars in self.variant_multi_pars:
            if not (variant_request_type := self.__get_variant_request_type(v_pars)):
                continue

            # a bit verbose for now...
            if "variantFusionRequest" in variant_request_type:
                if (q := self.__create_variantFusionRequest_query(v_pars)):
                    queries.append(q)
                    continue
            if "geneVariantRequest" in variant_request_type:
                if (q := self.__create_geneVariantRequest_query(v_pars)):
                    queries = [*queries, *q]
                    continue
            if "cytoBandRequest" in variant_request_type:
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
            if "variantTypeFilteredRequest" in variant_request_type:
                if (q := self.__create_variantTypeRequest_query(v_pars)):
                    queries.append(q)
                    continue

        # if len(queries) == 1:
        #     queries = queries[0]

        prdbug(f'__loop_multivars queries: {queries}')

        return queries


    ################################################################################

    def __get_variant_request_type(self, v_pars):
        """
        This method guesses the type of variant request, based on the complete
        fulfillment of the required parameters (all of `all_of`, one if `one_of`).
        In case of multiple types the one with most matched parameters is prefered.
        This may be changed to using a pre-defined request type and using this as
        completeness check only.
        TODO: Verify by schema ...
        TODO: This is all a bit too complex; probbaly better to just do it as a
              stack of dedicated tests and including a "defined to fail" query
              which is only removed after a successfull type match.
        """

        variant_request_type = None

        brts = self.variant_request_definitions.get("request_types", {})
        brts_k = brts.keys()
        # prdbug(f'...brts_k: {brts_k}')
        
        # Already hard-coding some types here - if conditions are met only
        # the respective types will be evaluated since only this key is used
        if "mate_name" in  v_pars:
            brts_k = [ "variantFusionRequest" ]
        elif "start" in v_pars and "end" in v_pars:
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
        elif "variant_type" in v_pars and len(self.filters) > 0:
            brts_k = [ "variantTypeFilteredRequest" ]
            
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

        prdbug(f'...variant_request_type: {variant_request_type}')
        return variant_request_type


    #--------------------------------------------------------------------------#

    def __create_geneVariantRequest_query(self, v_pars):
        # query database for gene and use coordinates to create range query
        gene_id = v_pars.get("gene_id", [])
        prdbug(f'...geneVariantRequest gene_id: {gene_id}')
        queries = []
        for g in gene_id:
            # TODO: error report/warning
            if not (gene_data := GeneInfo().returnGene(g)):
                continue
            gene = gene_data[0]
            prdbug(f'...geneVariantRequest gene_data: {gene}')
            # Since this is a pre-processor to the range request
            v_pars.update({
                "reference_name": f'refseq:{gene.get("accession_version", "___none___")}',
                "start": [ gene.get("start", 0) ],
                "end": [ gene.get("end", 1) ]
            })
            q_t = self.__create_variantRangeRequest_query(v_pars)
            prdbug(f'...geneVariantRequest query result: {q_t}')
            queries.append(q_t)

        if len(queries) < 1:
            return False

        return queries

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
        CB = Cytobands()
        cbs, chro, start, end = CB.bands_from_cytostring(cb_s)
        sequence_id = self.self.ChroNames.refseq(chro)
        v_pars.update( {
            "reference_name": sequence_id,
            "start": [start],
            "end": [end]
        } )
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

    def __create_variantFusionRequest_query(self, v_pars):    
        vp = v_pars
        v_p_defs = self.argument_definitions

        # here we use the db fields of "mate_..." for all positional parameters
        # since the match is against the `adjuncture` variant format
        v_q = {
            "$and": [
                {
                    v_p_defs["mate_name"]["db_key"]: vp["reference_name"],
                    v_p_defs["mate_start"]["db_key"]: { "$lt": vp["end"][-1] },
                    v_p_defs["mate_end"]["db_key"]: { "$gte": vp["start"][0] }
                },
                {
                    v_p_defs["mate_name"]["db_key"]: vp["mate_name"],
                    v_p_defs["mate_start"]["db_key"]: { "$lt": vp["mate_end"][-1] },
                    v_p_defs["mate_end"]["db_key"]: { "$gte": vp["mate_start"][0] }
                }
            ]
        }

        if (l_q := self.__request_variant_size_limits(v_pars)):
            v_q.update(l_q)

        p_n = "variant_type"
        if p_n in vp:
            v_q.update( self.__create_in_query_for_parameter(p_n, v_p_defs[p_n]["db_key"], vp) )

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
        v_p_defs = self.argument_definitions

        v_q = {
            v_p_defs["reference_name"]["db_key"]: vp["reference_name"],
            v_p_defs["start"]["db_key"]: { "$gte": sorted(vp["start"])[0], "$lt": sorted(vp["start"])[-1] },
            v_p_defs["end"]["db_key"]: { "$gte": sorted(vp["end"])[0], "$lt": sorted(vp["end"])[-1] },
        }

        if (v_t := self.__create_in_query_for_parameter("variant_type", v_p_defs["variant_type"]["db_key"], vp)):
            v_q.update(v_t)

        return v_q


    #--------------------------------------------------------------------------#

    def __create_variantAlleleRequest_query(self, v_pars):
        """
     
        """
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
        if len(self.filters) < 1:
            return

        logic = self.__boolean_to_mongo_logic(BYC_PARS.get("filter_logic"))

        data_db = MongoClient(host=DB_MONGOHOST)[self.ds_id]
        coll_coll = data_db[ self.filtering_terms_coll ]
        self.collation_ids = coll_coll.distinct("id", {})

        f_lists = {}
        f_infos = {}

        for i, f in enumerate(self.filters):
            f = self.__substitute_filter_id(f)
            f_val = f.get("id")
            prdbug(f_val)
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

            # TODO: needs a general solution for alphanumerics; so far for the
            # iso age w/ pre-calculated days field...
            if "alphanumeric" in f_info.get("type", "ontology"):
                prdbug(f'__query_from_filters ... alphanumeric: {f_info["id"]}')
                if re.match(r'^(\w+):([<>=]+?)?(\w[\w.]+?)$', f_info["id"]):
                    f_class, comp, val = re.match(r'^(\w+):([<>=]+?)?(\w[\w.]+?)$', f_info["id"]).group(1, 2, 3)
                    if "iso8601duration" in f_info.get("format", "___none___"):
                        val = days_from_iso8601duration(val)
                    f_lists[f_entity][f_field].append(self.__mongo_comparator_query(comp, val))
                else:
                    f_lists[f_entity][f_field].append(f_info["id"])
            elif f_desc is True:
                if f_neg is True:
                    f_lists[f_entity][f_field].append({'$nin': f_info["child_terms"]})
                else:
                    f_lists[f_entity][f_field].append({'$in': f_info["child_terms"]})
            else:
                if f_neg is True:
                    f_lists[f_entity][f_field].append({'$nin': [f_info["id"]]})
                else:
                    f_lists[f_entity][f_field].append(f_info["id"])
            prdbug(f'... f_neg: {f_neg} ==>> f_field: {f_lists[f_entity][f_field]}')

        # now processing the filter lists into the queries

        for f_entity in f_lists.keys():
            f_s_l = []
            for f_field, f_query_vals in f_lists[f_entity].items():
                if len(f_query_vals) == 1:
                    f_s_l.append({f_field: f_query_vals[0]})
                else:
                    for f_q_v in f_query_vals:
                        f_s_l.append({f_field: f_q_v})

            self.__update_queries_for_entity(f_s_l, f_entity)

    # -------------------------------------------------------------------------#

    def __substitute_filter_id(self, f):
        f.update({"id": f.get("id", "___none___").replace("PMID:", "pubmed:")})
        return f


    # -------------------------------------------------------------------------#

    def __query_from_collationed_filter(self, coll_coll, f_val):
        f_d_s = BYC["filter_definitions"].get("$defs", {})
        if f_val not in self.collation_ids:
            return False

        f_info = coll_coll.find_one({"id": f_val}, {"frequencymap": 0})
        f_ct = f_info.get("collation_type", "___none__")
        if not (f_d := f_d_s.get(f_ct)):
            return False

        # TODO: the whole "get entity" is a bit cumbersome ... should be added
        # to each collation in the next generation round
        f_info.update({"entity": f_d.get("entity", "biosample")})

        return f_info


    # -------------------------------------------------------------------------#

    def __query_from_filter_definitions(self, f_val):
        f_d_s = BYC["filter_definitions"].get("$defs", {})
        f_info = {
            "id": f_val,
            "scope": "biosamples",
            "type": "___undefined___",
            "db_key": "___undefined___",
            "child_terms": [f_val]
        }

        prdbug(f'...__query_from_filter_definitions: {f_val}')

        for f_d in f_d_s.values():
            if f_d.get("collationed", False) is True:
                continue
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
        geo_q = GeoQuery().get_geoquery()
        if not geo_q:
            return
        self.__update_queries_for_entity([geo_q], entity)


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

        t_v = h_o["target_values"]
        c_n = h_o["collection"]
        t_e = h_o["entity_id"]
        t_c = h_o["target_count"]

        t_v = return_paginated_list(t_v, self.skip, self.limit)
        if len(t_v) < 1:
            return
        h_o_q = [{"id": {'$in': t_v}}]
        self.__update_queries_for_entity(h_o_q, t_e)


    # -------------------------------------------------------------------------#

    def __update_queries_for_entity(self, query, entity):
        # TODO: This is now for using generally query lists and aggregate 
        # by multiple queries & intersection of matched ids during execution
        # => logic right now always AND
        logic = self.__boolean_to_mongo_logic(BYC_PARS.get("filter_logic"))
        r_t_s = self.response_types
        r_c = r_t_s[entity].get("collection")
        q_e = self.queries.get("entities")

        if type(query) is not list:
            query = [query]


        if entity not in q_e:
            q_e.update({entity:{"query": query, "collection": r_c}})
        else:
            q_e[entity]["query"] = [*q_e[entity]["query"], *query]

        # if entity not in q_e:
        #     q_e.update({entity:{"query": query, "collection": r_c}})
        # elif logic in q_e[entity]["query"]:
        #     q_e[entity]["query"][logic].append(query)
        # else:
        #     q_e[entity].update({"query": {logic: [q_e[entity]["query"], query]}})

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

class GeoQuery():
    """
    This class is used to generate a query for the geolocation data.
    It is an extension of the standard BeaconQuery process.
    """

    def __init__(self, geo_root="geo_location"):
        self.argument_definitions = BYC.get("argument_definitions", {}).get("parameters", {})
        
        # this is a remnant of geo objects in different nestings...
        self.geo_root = geo_root
        self.geo_dot_keys = {
            "properties": "properties",
            "geometry": "geometry"
        }
        if len(self.geo_root) > 0:
            for k, v in self.geo_dot_keys.items():
                self.geo_dot_keys[k] = ".".join([self.geo_root, v])

        self.geo_pars = {
            "city": None,
            "country": None,
            "iso3166alpha2": None,
            "iso3166alpha3": None,
            "geo_latitude": None,
            "geo_longitude": None,
            "geo_distance": None
        }

        self.__get_geo_pars()

        self.query = {
            "expand": True,
            "geo_query": {}
        }

        self.__geo_city_query()
        self.__geo_geo_longlat_query()

#         self.query = mongo_and_or_query_from_list(geoq_l)


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def get_geoquery(self):
        return self.query.get("geo_query", {})


    # -------------------------------------------------------------------------#

    def get_geopars(self):
        return self.geo_pars


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __get_geo_pars(self):
        """
        This method retrieves the geolocation parameters from the general
        parameters object.
        """
        g_k_s = list(self.geo_pars.keys())

        for p_k, p_v_s in BYC_PARS.items():
            if not p_k in g_k_s:
                continue
            self.geo_pars.update({p_k: p_v_s})

        # remove all keys with empty values
        for g_k in g_k_s:
            if not self.geo_pars.get(g_k):
                self.geo_pars.pop(g_k, None)

        prdbug(f'...__get_geo_pars: {self.geo_pars}')



    # -------------------------------------------------------------------------#

    def __geo_geo_longlat_query(self):
        if self.query.get("expand") is not True:
            return

        for g_k in ["geo_latitude", "geo_longitude", "geo_distance"]:
            if not self.geo_pars.get(g_k):
                return

        geoq_l = [ {
            self.geo_dot_keys["geometry"]: {
                '$near': SON(
                    [
                        (
                            '$geometry', SON(
                                [
                                    ('type', 'Point'),
                                    ('coordinates', [
                                        self.geo_pars.get("geo_longitude"),
                                        self.geo_pars.get("geo_latitude")
                                    ])
                                ]
                            )
                        ),
                        ('$maxDistance', self.geo_pars.get("geo_distance"))
                    ]
                )
            }
        } ]

        self.query.update({
            "geo_query": mongo_and_or_query_from_list(geoq_l),
            "expand": False
        })


    # -------------------------------------------------------------------------#

    def __geo_city_query(self):
        if self.query.get("expand") is not True:
            return
        if len(city_v := self.geo_pars.get("city", "")) < 1:
            return

        geoq_l = [
            {f'{self.geo_dot_keys["properties"]}.city': re.compile(r'^' + str(city_v), re.IGNORECASE)}
        ]

        for g_k in ["country", "iso3166alpha3", "iso3166alpha2"]:
            if len(g_v := self.geo_pars.get(g_k, "")) < 1:
                continue

            geoq_l.append(
                {f'{self.geo_dot_keys["properties"]}.{g_k}': re.compile(r'^' + str(g_v) + r'$', re.IGNORECASE)}
            )

        self.query.update({
            "geo_query": mongo_and_or_query_from_list(geoq_l),
            "expand": False
        })


################################################################################
################################################################################
################################################################################

