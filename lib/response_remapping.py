import datetime, re
from pymongo import MongoClient
from cgi_parsing import *

################################################################################

def reshape_resultset_results(ds_id, r_s_res, byc):

    r_s_res = remap_variants(r_s_res, byc)
    r_s_res = remap_analyses(r_s_res, byc)
    r_s_res = remap_biosamples(r_s_res, byc)
    r_s_res = remap_cohorts(r_s_res, byc)
    r_s_res = remap_individuals(r_s_res, byc)
    r_s_res = remap_phenopackets(ds_id, r_s_res, byc)
    r_s_res = remap_runs(r_s_res, byc)
    r_s_res = remap_all(r_s_res)

    return r_s_res

################################################################################

def remap_variants(r_s_res, byc):

    """
    Since the Beacon default model works from the concept of a canonical genomic
    variation and the bycon data model uses variant instances, the different
    instances of a "canonical" variant have to be identified and grouped together
    with individual instances indicated through their identifiers in `caseLevelData`.
    """
    if not "genomicVariant" in byc["response_entity_id"]:
        return r_s_res

    v_d = byc["variant_definitions"]

    variant_ids = []
    for v in r_s_res:
        try:
            variant_ids.append(v["variant_internal_id"])
        except:
            pass
    variant_ids = list(set(variant_ids))

    variants = []

    for d in variant_ids:

        d_vs = [v for v in r_s_res if v['variant_internal_id'] == d]

        v = { "variation": d_vs[0], "case_level_data": [] }

        for d_v in d_vs:
            v["case_level_data"].append(
                {   
                    "id": d_v["id"],
                    "biosample_id": d_v["biosample_id"],
                    "analysis_id": d_v["callset_id"]
                }
            )

        # TODO: Keep legacy pars?
        legacy_pars = ["_id", "id", "reference_name", "type", "biosample_id", "callset_id", "individual_id", "info", "variant_type", "variant_state", "reference_bases", "alternate_bases", "start", "end"]
        for p in legacy_pars:
            v["variation"].pop(p, None)

        variants.append(v)

    return variants
    
################################################################################

def remap_analyses(r_s_res, byc):

    if not "analysis" in byc["response_entity_id"]:
        return r_s_res

    pop_keys = ["info", "provenance", "cnv_statusmaps", "cnv_chro_stats", "cnv_stats"]

    if "stats" in byc["output"]:
        pop_keys = ["info", "provenance", "cnv_statusmaps"]

    for cs_i, cs_r in enumerate(r_s_res):
        # TODO: REMOVE VERIFIER HACKS
        r_s_res[cs_i].update({"pipeline_name": "progenetix", "analysis_date": "1967-11-11" })
        for k in pop_keys:
            r_s_res[cs_i].pop(k, None)

    return r_s_res

################################################################################

def remap_cohorts(r_s_res, byc):

    if not "cohort" in byc["response_entity_id"]:
        return r_s_res

    cohorts = [ ]

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

def remap_runs(r_s_res, byc):

    if not "run" in byc["response_entity_id"]:
        return r_s_res

    runs = []
    for cs_i, cs_r in enumerate(r_s_res):
        r = {
                "id": cs_r.get("id", ""),
                "analysis_id": cs_r.get("id", ""),
                "biosample_id": cs_r.get("biosample_id", ""),
                "individual_id": cs_r.get("individual_id", ""),
                "run_date": datetime.datetime.fromisoformat(cs_r.get("updated", datetime.datetime.now().isoformat())).isoformat()
            }
        runs.append(r)

    return runs

################################################################################

def remap_biosamples(r_s_res, byc):

    if not "biosample" in byc["response_entity_id"]:
        return r_s_res

    for bs_i, bs_r in enumerate(r_s_res):

        # TODO: REMOVE VERIFIER HACKS
        r_s_res[bs_i].update({"sample_origin_type": { "id": "OBI:0001479", "label": "specimen from organism"} })

        for f in ["tumor_grade", "pathological_stage", "histological_diagnosis"]:
            try:
                if f in r_s_res[bs_i]:
                    if not r_s_res[bs_i][f]:
                        r_s_res[bs_i].pop(f)
                    elif not r_s_res[bs_i][f]["id"]:
                        r_s_res[bs_i].pop(f)
                    elif len(r_s_res[bs_i][f]["id"]) < 4:
                        r_s_res[bs_i].pop(f)
            except:
                pass

    return r_s_res

################################################################################

def remap_individuals(r_s_res, byc):

    if not "individual" in byc["response_entity_id"]:
        return r_s_res

    return r_s_res

################################################################################

def remap_phenopackets(ds_id, r_s_res, byc):

    if not "phenopacket" in byc["response_entity_id"]:
        return r_s_res

    mongo_client = MongoClient()
    data_db = mongo_client[ds_id]
    pxf_s = []

    for ind_i, ind in enumerate(r_s_res):

        pxf = phenopack_individual(ind, data_db, byc)

        pxf_s.append(pxf)

    return pxf_s

################################################################################

def phenopack_individual(ind, data_db, byc):

    # TODO: key removal based on the ones not part of the respective PXF schemas
    # or better on filling them in only for existing parameters

    pxf_bios = []

    pxf_resources = _phenopack_resources(byc)
    server = select_this_server( byc )

    bios_s = data_db["biosamples"].find({"individual_id":ind["id"]})

    for bios in bios_s:

        bios.update({
            "files": [
                {
                    "uri": "{}/beacon/biosamples/{}/variants/?output=pgxseg".format(server, bios["id"]),
                    "file_attributes": {
                        "genomeAssembly": "GRCh38",
                        "fileFormat": "pgxseg"
                    }
                }
            ]
        })
        for k in ["info", "provenance", "_id", "followup_time", "followup_state", "cohorts", "icdo_morphology", "icdo_topography"]:
            bios.pop(k, None)
        pxf_bios.append(bios)

    pop_keys = ["_id", "provenance"]

    for k in pop_keys:
        ind.pop(k, None)

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

def _phenopack_resources(byc):

    # TODO: make thsi general, at least for phenopacket response, and only scan used prefixes

    f_d = byc["filter_definitions"]
    rkeys = ["NCITgrade", "NCITstage", "NCITtnm", "NCIT", "PATOsex", "EFOfus" ]

    pxf_rs = []

    for r_k in rkeys:
        if r_k not in f_d.keys():
            continue

        d = f_d[r_k]

        pxf_r = {
          "id": r_k,
          "name": d.get("name", ""),
          "url": d.get("url", ""),
          "namespace_prefix": d.get("namespace_prefix", ""),
          "version": "2022-04-01",
          "iri_prefix": "http://purl.obolibrary.org/obo/{}_".format( d.get("namespace_prefix", "") )
        }

        pxf_rs.append(pxf_r)

    return pxf_rs

################################################################################

def remap_all(r_s_res):

    for br_i, br_r in enumerate(r_s_res):
        r_s_res[br_i].pop("_id", None)
        r_s_res[br_i].pop("description", None)

    return r_s_res



################################################################################

def normalize_variant_values_for_export(v, byc, drop_fields=None):

    drop_fields = [] if drop_fields is None else drop_fields

    v_defs = byc["variant_definitions"]

    v["log2"] = False
    if "info" in v:
        if "cnv_value" in v["info"]:
            if isinstance(v["info"]["cnv_value"],float):
                v["log2"] = round(v["info"]["cnv_value"], 3)
        if not "info" in drop_fields:
            drop_fields.append("info")

    if v["log2"] == False:
        if "variant_type" in v:
            if v["variant_type"] in v_defs["cnv_dummy_values"].keys():
                v["log2"] = v_defs["cnv_dummy_values"][ v["variant_type"] ]

    if v["log2"] == False:
        drop_fields.append("log2")

    v["start"] = int(v["start"])
    v["end"] = int(v["end"])

    for d_f in drop_fields:   
        v.pop(d_f, None)

    return v


