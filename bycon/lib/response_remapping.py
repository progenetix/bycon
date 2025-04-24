import re
from copy import deepcopy
from datetime import datetime
from deepmerge import always_merger
from pymongo import MongoClient
from os import environ
from isodate import date_isoformat

from bycon_helpers import prdbug, clean_empty_fields, select_this_server
from config import *
from variant_mapping import ByconVariant

################################################################################
################################################################################
################################################################################

def reshape_resultset_results(ds_id, r_s_res):
    if (variants := VariantsResponse(r_s_res).beaconVariants()):
        return variants
    r_s_res = remap_analyses(r_s_res)
    r_s_res = remap_biosamples(r_s_res)
    r_s_res = remap_cohorts(r_s_res)
    r_s_res = remap_individuals(r_s_res)
    r_s_res = remap_phenopackets(ds_id, r_s_res)
    r_s_res = remap_runs(r_s_res)
    return remap_all(r_s_res)


################################################################################

class VariantsResponse:

    def __init__(self, pgxvars=[]):
        self.pgx_vars = pgxvars
        self.VAR = ByconVariant()
        self.beacon_vars = []
        self.case_pars = ["biosample_id", "analysis_id", "individual_id", "run_id"]
        self.var_pars = ["identifiers", "molecular_attributes", "variant_level_data"]


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def beaconVariants(self):
        if not "genomicVariant" in BYC["response_entity_id"]:
            return False
        self.__remap_vars_4_beacon()
        return self.beacon_vars


    # -------------------------------------------------------------------------#
    # ---------------------------- private ------------------------------------#
    # -------------------------------------------------------------------------#

    def __remap_vars_4_beacon(self):
        variant_ids = set()
        for v in self.pgx_vars:
            if (viid := v.get("variant_internal_id")):
                variant_ids.add(viid)
        variant_ids = list(variant_ids)

        for d in variant_ids:
            d_vs = [var for var in self.pgx_vars if var.get('variant_internal_id', "__none__") == d]

            v_i = deepcopy(self.VAR.vrsVariant(d_vs[0]))
            for c_k in self.case_pars + ["variant_internal_id", "info"] + self.var_pars:
                v_i.pop(c_k, None)
            v_i = clean_empty_fields(v_i)

            v = {
                "variation": v_i,
                "case_level_data": [],
                "variant_internal_id": d
            }

            for v_k in self.var_pars:
                v.update({v_k: {}})

            for d_v in d_vs:
                c_l_v = {}
                for c_k in self.case_pars:
                    if (c_v := d_v.get(c_k)):
                        c_l_v.update({c_k: c_v})
                if (id_v := d_v.get("id")):
                    c_l_v.update({"variant_id": id_v})
                v["case_level_data"].append(c_l_v)

                for v_k in self.var_pars:
                    if (v_v := d_v.get(v_k)):
                        v[v_k].update(always_merger.merge(v[v_k], v_v))

            self.beacon_vars.append(v)


    # -------------------------------------------------------------------------#
    # ----------------------- / VariantsResponse ------------------------------#
    # -------------------------------------------------------------------------#


################################################################################

def remap_analyses(r_s_res):
    if not "analysis" in BYC["response_entity_id"]:
        return r_s_res
    pop_keys = ["info", "geo_location", "cnv_statusmaps", "cnv_chro_stats", "cnv_stats"]
    # TODO: move the cnvstats option away from here
    if "cnvstats" in str(BYC_PARS.get("request_entity_path_id")):
        pop_keys = ["info", "cnv_statusmaps"]

    for cs_i, cs_r in enumerate(r_s_res):
        # TODO: REMOVE VERIFIER HACKS (partially done...)
        p_i = cs_r.get("pipeline_info", {"id": "progenetix"})
        r_s_res[cs_i].update({
            "pipeline_name": p_i.get("id", "progenetix"),
            "analysis_date": cs_r.get("analysis_date", date_isoformat(datetime.now()))
        })
        for k in pop_keys:
            r_s_res[cs_i].pop(k, None)
    return r_s_res


################################################################################

def remap_cohorts(r_s_res):
    if not "cohort" in BYC["response_entity_id"]:
        return r_s_res

    cohorts = []

    # TODO: expand parameters by adding more pre-computed to collations (individual counts ...)

    for cs_i, cs_r in enumerate(r_s_res):
        cohorts.append({
            "cohort_id": cs_r.get("id", cs_i),
            "cohort_type": "beacon-defined",
            "cohort_name": cs_r.get("label", ""),
            "cohort_size": int(cs_r.get("count", 0))
        })

    return cohorts


################################################################################

def remap_runs(r_s_res):
    if not "run" in BYC["response_entity_id"]:
        return r_s_res

    runs = []
    for ana in r_s_res:
        r = {
            "id": ana.get("id", ""),
            "individual_id": ana.get("individual_id", ""),
            "run_date": datetime.fromisoformat(
                ana.get("updated", datetime.now().isoformat())).isoformat()
        }
        for p in ["biosample_id", "individual_id", "platform_model"]:
            if (v := ana.get(p)):
                r.update({p: v})
        runs.append(r)

    return runs


################################################################################

def remap_biosamples(r_s_res):
    if not "biosample" in BYC["response_entity_id"]:
        return r_s_res
    if not r_s_res:
        return None

    bs_pop_keys = ["_id", "followup_state", "followup_time", "references"]  # "info"
    r_s_u = []
    for bs_i, bs_r in enumerate(r_s_res):
        # some none results might have crept in?
        if type(bs_r) is not dict:
            continue
        # TODO: REMOVE VERIFIER HACKS
        bs_r.update({
            "sample_origin_type": {"id": "OBI:0001479", "label": "specimen from organism"},
            "external_references": []
        })
        if (b_r_s := bs_r.get("references")):
            for r_k, r_v in b_r_s.items():
                if (r_i := __reference_object_from_ontology_term(r_k, r_v)):
                    bs_r["external_references"].append(r_i)

        for f in ["tumor_grade", "pathological_stage", "histological_diagnosis"]:
            try:
                if f in bs_r:
                    if not bs_r[f]:
                        bs_r.pop(f, None)
                    elif not bs_r[f]["id"]:
                        bs_r.pop(f, None)
                    elif len(bs_r[f]["id"]) < 4:
                        bs_r.pop(f, None)
            except:
                pass
        for k in bs_pop_keys:
            bs_r.pop(k, None)
        r_s_u.append(bs_r)

    r_s_res = r_s_u
    return r_s_res


################################################################################

def __reference_object_from_ontology_term(filter_type, ontology_term):
    f_d_s = BYC["filter_definitions"].get("$defs", {})
    if "label" in ontology_term:
        ontology_term.update({"description": ontology_term.get("label", "")})
        ontology_term.pop("label", None)
    f_t_d = f_d_s.get(filter_type, {})
    if not (r_d := f_t_d.get("reference")):
        return ontology_term
    r_r = r_d.get("replace", [])
    if len(r_r) == 2:
        o_id = ontology_term.get("id", "___none___").replace(r_r[0], r_r[1])
    ontology_term.update({"reference": f'{r_d.get("root")}{o_id}'})
    return ontology_term


################################################################################

def remap_individuals(r_s_res):
    if not "individual" in BYC["response_entity_id"]:
        return r_s_res

    ind_s = []
    for ind_i, ind in enumerate(r_s_res):
        individual_remap_pgx_diseases(ind)
        ind_s.append(ind)

    return ind_s


################################################################################

def remap_phenopackets(ds_id, r_s_res):
    if not "phenopacket" in BYC["response_entity_id"]:
        return r_s_res

    mongo_client = MongoClient(host=DB_MONGOHOST)
    data_db = mongo_client[ds_id]
    pxf_s = []

    for ind_i, ind in enumerate(r_s_res):
        pxf = phenopack_individual(ind, data_db)
        pxf_s.append(pxf)

    return pxf_s


################################################################################

def phenopack_individual(ind, data_db):
    # TODO: key removal based on the ones not part of the respective PXF schemas
    # or better on filling them in only for existing parameters

    pxf_bios = []
    ind_pop_keys = ["_id", "geo_location", "external_references", "description", "info"]
    bs_pop_keys = ["info", "geo_location", "_id", "followup_time", "followup_state", "cohorts", "icdo_morphology",
                   "icdo_topography"]

    pxf_resources = _phenopack_resources()
    server = select_this_server()

    bios_s = data_db["biosamples"].find({"individual_id": ind.get("id", "___none___")})

    for bios in bios_s:
        e_r = []
        for r_k, r_v in bios.get("references", {}).items():
            e_r.append(__reference_object_from_ontology_term(r_k, r_v))
        bios.update({
            "external_references" : e_r,
            "files": [
                {
                    "uri": f'{server}/services/vcfvariants/{bios.get("id", "___none___")}',
                    "file_attributes": {
                        "genomeAssembly": "GRCh38",
                        "fileFormat": "VCF"
                    }
                }
            ]
        })
        for k in bs_pop_keys:
            bios.pop(k, None)
        clean_empty_fields(bios)
        pxf_bios.append(bios)

    for k in ind_pop_keys:
        ind.pop(k, None)

    individual_remap_pgx_diseases(ind)
    for d_i, d in enumerate(ind["diseases"]):
        for k in ["followup_state", "followup_time"]:
            ind["diseases"][d_i].pop(k, None)

    pxf = {
        "id": re.sub("pgxind", "pgxpxf", ind["id"]),
        "subject": ind,
        "biosamples": pxf_bios,
        "metaData": {
            "submitted_by": "@mbaudis",
            "phenopacket_schema_version": "v2",
            "resources": pxf_resources
        }
    }

    return pxf


################################################################################

def individual_remap_pgx_diseases(ind):
    # TODO: This should be more general, i.e. what is mapped/how, deleted...

    diseases = []

    for k in ["index_disease", "auxiliary_disease"]:
        try:
            if len(ind[k]["disease_code"]["id"]) > 1:
                diseases.append(ind[k])
        except:
            pass
        ind.pop(k, None)

    ind.update({"diseases": diseases})
    return ind


################################################################################

def _phenopack_resources():
    # TODO: make this general, at least for phenopacket response, and only scan used prefixes
    f_d_s = BYC["filter_definitions"].get("$defs", {})
    # rkeys = ["NCITgrade", "NCITstage", "NCITtnm", "NCIT", "PATOsex", "EFOfus" ]
    rkeys = ["NCIT", "NCITsex", "EFOfus", "UBERON"]
    pxf_rs = []
    for r_k in rkeys:
        if not (d := f_d_s.get(r_k)):
            continue

        pxf_r = {
            "id": r_k,
            "name": d.get("name", ""),
            "url": d.get("url", ""),
            "namespace_prefix": d.get("namespace_prefix", ""),
            "version": "2022-04-01",
            "iri_prefix": "http://purl.obolibrary.org/obo/{}_".format(d.get("namespace_prefix", ""))
        }

        pxf_rs.append(pxf_r)

    return pxf_rs


################################################################################

def remap_all(r_s_res):
    if not r_s_res:
        return None
    for br_i, br_r in enumerate(r_s_res):
        if type(br_r) is not dict:
            continue
        r_s_res[br_i].pop("_id", None)
        clean_empty_fields(r_s_res[br_i])

    return r_s_res

