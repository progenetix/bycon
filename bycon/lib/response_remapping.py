import datetime, re
from pymongo import MongoClient

from bycon_helpers import prdbug, select_this_server
from config import *
from variant_mapping import ByconVariant
from os import environ

################################################################################
################################################################################
################################################################################

def reshape_resultset_results(ds_id, r_s_res):
    r_s_res = remap_variants(r_s_res)
    r_s_res = remap_analyses(r_s_res)
    r_s_res = remap_biosamples(r_s_res)
    r_s_res = remap_cohorts(r_s_res)
    r_s_res = remap_individuals(r_s_res)
    r_s_res = remap_phenopackets(ds_id, r_s_res)
    r_s_res = remap_runs(r_s_res)
    r_s_res = remap_all(r_s_res)

    return r_s_res


################################################################################

def remap_variants(r_s_res):
    """
    Since the Beacon default model works from the concept of a canonical genomic
    variation and the bycon data model uses variant instances, the different
    instances of a "canonical" variant have to be identified and grouped together
    with individual instances indicated through their identifiers in `caseLevelData`.
    """

    if not "genomicVariant" in BYC["response_entity_id"]:
        return r_s_res

    # TODO: still used???
    special_output = BYC_PARS.get("output", "___none___").lower()

    if "vcf" in special_output or "pgxseg" in special_output:
        return r_s_res

    variant_ids = []
    for v in r_s_res:
        variant_ids.append(v["variant_internal_id"])
    variant_ids = list(set(variant_ids))

    variants = []

    for d in variant_ids:
        d_vs = [var for var in r_s_res if var.get('variant_internal_id', "__none__") == d]
        v = {
            "variant_internal_id": d,
            "variation": ByconVariant().vrsVariant(d_vs[0]), "case_level_data": []
        }
        for d_v in d_vs:
            c_l_v = {}
            for c_k in ("id", "biosample_id", "analysis_id", "individual_id", "info"):
                if (c_v := d_v.get(c_k)):
                    c_l_v.update({c_k: c_v})
            v["case_level_data"].append(c_l_v)

        # TODO: Keep legacy pars?
        legacy_pars = ["_id", "id", "variant_internal_id", "reference_name", "type", "biosample_id", "analysis_id", "individual_id",
                       "variant_type", "reference_bases", "alternate_bases", "start", "end", "required", "info"]
        for p in legacy_pars:
            v["variation"].pop(p, None)

        for k in ["molecular_attributes", "variant_level_data", "identifiers"]:
            k_v = v["variation"].get(k)
            if not k_v:
                 v["variation"].pop(k, None)
        for k in ["variant_alternative_ids"]:
            if len(v["variation"].get(k, [])) < 1:
                v["variation"].pop(k, None)

        variants.append(v)

    return variants


################################################################################

def remap_analyses(r_s_res):
    if not "analysis" in BYC["response_entity_id"]:
        return r_s_res
    pop_keys = ["info", "provenance", "cnv_statusmaps", "cnv_chro_stats", "cnv_stats"]
    if "cnvstats" in BYC_PARS.get("output", "___none___").lower():
        pop_keys = ["info", "provenance", "cnv_statusmaps"]

    for cs_i, cs_r in enumerate(r_s_res):
        # TODO: REMOVE VERIFIER HACKS
        r_s_res[cs_i].update({"pipeline_name": "progenetix", "analysis_date": "1967-11-11"})
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
            "run_date": datetime.datetime.fromisoformat(
                ana.get("updated", datetime.datetime.now().isoformat())).isoformat()
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
    for bs_i, bs_r in enumerate(r_s_res):
        # TODO: REMOVE VERIFIER HACKS
        e_r = []
        for r_k, r_v in bs_r.get("references", {}).items():
            if (r_i := __reference_object_from_ontology_term(r_k, r_v)):
                e_r.append(r_i)

        r_s_res[bs_i].update({
            "sample_origin_type": {"id": "OBI:0001479", "label": "specimen from organism"},
            "external_references": e_r
        })
        for f in ["tumor_grade", "pathological_stage", "histological_diagnosis"]:
            try:
                if f in r_s_res[bs_i]:
                    if not r_s_res[bs_i][f]:
                        r_s_res[bs_i].pop(f, None)
                    elif not r_s_res[bs_i][f]["id"]:
                        r_s_res[bs_i].pop(f, None)
                    elif len(r_s_res[bs_i][f]["id"]) < 4:
                        r_s_res[bs_i].pop(f, None)
            except:
                pass
        for k in bs_pop_keys:
            r_s_res[bs_i].pop(k, None)
    return r_s_res


################################################################################

def __reference_object_from_ontology_term(filter_type, ontology_term):
    f_d_s = BYC.get("filter_definitions", {})
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
    ind_pop_keys = ["_id", "provenance", "external_references", "description", "info"]
    bs_pop_keys = ["info", "provenance", "_id", "followup_time", "followup_state", "cohorts", "icdo_morphology",
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

def clean_empty_fields(this_object):
    protected = ["external_references"]
    if not isinstance(this_object, dict):
        return this_object

    for k in list(this_object.keys()):
        if k in protected:
            continue
        if isinstance(this_object[k], dict):
            if not this_object[k]:
                this_object.pop(k, None)
        elif isinstance(this_object[k], list):
            if len(this_object[k]) < 1:
                this_object.pop(k, None)

    return this_object


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
    f_d_s = BYC.get("filter_definitions", {})
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

