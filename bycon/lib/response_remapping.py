import datetime, re
from pymongo import MongoClient
from cgi_parsing import *

################################################################################

def reshape_resultset_results(ds_id, r_s_res, byc):

    r_s_res = remap_variants_to_VCF(r_s_res, byc)
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

    if not "variant" in byc["response_entity_id"].lower():
        return r_s_res
    if "vcf" in byc["output"].lower():
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

        d_vs = [var for var in r_s_res if var.get('variant_internal_id', "__none__") == d]

        v = { 
            "variant_internal_id": d,
            "variation": d_vs[0], "case_level_data": []
        }

        v["variation"].pop("variant_internal_id", None)

        for d_v in d_vs:
            v["case_level_data"].append(
                {   
                    "id": d_v.get("id", "__none__"),
                    "biosample_id": d_v.get("biosample_id", "__none__"),
                    "analysis_id": d_v.get("callset_id", "__none__")
                }
            )

        # TODO: Keep legacy pars?
        legacy_pars = ["_id", "id", "reference_name", "type", "biosample_id", "callset_id", "individual_id", "variant_type", "variant_state", "reference_bases", "alternate_bases", "start", "end"]
        for p in legacy_pars:
            v["variation"].pop(p, None)

        variants.append(v)

    return variants

################################################################################

def remap_variants_to_VCF(r_s_res, byc):

    """
    """

    if not "variant" in byc["response_entity_id"].lower():
        return r_s_res
    if not "vcf" in byc["output"].lower():
        return r_s_res

    open_text_streaming(byc["env"], "variants.vcf")
    print(
"""##fileformat=VCFv4.4
##ALT=<ID=DUP,Description="Duplication">
##ALT=<ID=DEL,Description="Deletion">
##INFO=<ID=END,Number=1,Type=Integer,Description="End position of the longest variant described in this record">
##INFO=<ID=SVLEN,Number=A,Type=Integer,Description="Length of structural variant">
##INFO=<ID=CN,Number=A,Type=Float,Description="Copy number of CNV/breakpoint">
##INFO=<ID=SVCLAIM,Number=A,Type=String,Description="Claim made by the structural variant call. Valid values are D, J, DJ for abundance, adjacency and both respectively">
##INFO=<ID=IMPRECISE,Number=0,Type=Flag,Description="Imprecise structural variation">
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">"""
        )

    v_d = byc["variant_definitions"]
    v_o = {
        "#CHROM": ".",
        "POS": ".",
        "ID": ".",
        "REF": ".",
        "ALT": ".",
        "QUAL": ".",
        "FILTER": "PASS",
        "FORMAT": "",
        "INFO": ""
    }

    variant_ids = []
    for v in r_s_res:
        variant_ids.append(v.get("variant_internal_id", "__none__"))

    biosample_ids = []
    for v in r_s_res:
        biosample_ids.append(v.get("biosample_id", "__none__"))

    variant_ids = list(set(variant_ids))
    biosample_ids = list(set(biosample_ids))

    for bsid in biosample_ids:
        v_o.update({bsid:"."})

    variants = []
    # variants.append("   ".join(v_o.keys()))
    print("   ".join(v_o.keys()))

    for d in variant_ids:

        d_vs = [var for var in r_s_res if var.get('variant_internal_id', "__none__") == d]

        vcf_v = vcf_variant(d_vs[0], v_o.copy(), byc)

        for bsid in biosample_ids:
            vcf_v.update({bsid: "." })

        for d_v in d_vs:
            b_i = d_v.get("biosample_id", "__none__")
            vcf_v.update({b_i: "0/1" })

        r_l = map(str, list(vcf_v.values()))
        # variants.append("   ".join(r_l))
        print("   ".join(r_l))

    exit()
    return variants
    
################################################################################

def vcf_variant(v, vcf_v, byc):

    v_d = byc["variant_definitions"]

    v = de_vrsify_variant(v, byc)
    if v is False:
        return v

    vcf_v.update({
        "#CHROM": v.get("reference_name", "."),
        "POS": v.get("start", 0) + 1,
        "ID": ".",
        "REF": v.get("reference_bases", "."),
        "ALT": v.get("alternate_bases", "."),
        "QUAL": ".",
        "FILTER": "PASS",
        "FORMAT": "GT",
        "INFO": ""
    })

    if "variant_type" in v:
        vcf_v.update({"ALT": "<{}>".format(v["variant_type"]) })
        v_l = v["end"] - v["start"]
        vcf_v.update({"INFO": "IMPRECISE;SVCLAIM=D;END={};SVLEN={}".format(v["end"], v_l) })


    return vcf_v

################################################################################

def de_vrsify_variant(v, byc):

    v_d = byc["variant_definitions"]

    r_n = v["location"].get("sequence_id")
    if r_n is None:
        return False

    v_r =  {
        "id": v["id"],
        "variant_internal_id": v.get("variant_intvernal_id"),
        "callset_id": v.get("callset_id"),
        "biosample_id": v.get("biosample_id"),
        "reference_bases": v.get("reference_bases", "."),
        "alternate_bases": v.get("alternate_bases", "."),
        "reference_name": v_d["refseq_chronames"][ r_n ],
        "start": v["location"]["interval"]["start"]["value"],
        "end": v["location"]["interval"]["end"]["value"],
        "info": v.get("info", {})
    }

    if "variant_state" in v:
        efo = v["variant_state"].get("id")
        try:
            v_r.update({"variant_type": v_d["efo_vrs_map"][ efo ]["DUPDEL"] })
        except:
            pass
    elif "state" in v:
        t = v["state"].get("type", "__none__")
        s = v["state"].get("sequence", "")
        if "LiteralSequenceExpression" in t:
            v_r.update({"alternate_bases": s })

    return v_r

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

    bs_pop_keys = ["_id", "followup_state", "followup_time"] # "info"

    for bs_i, bs_r in enumerate(r_s_res):

        # TODO: REMOVE VERIFIER HACKS
        r_s_res[bs_i].update({"sample_origin_type": { "id": "OBI:0001479", "label": "specimen from organism"} })

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
    ind_pop_keys = ["_id", "provenance", "external_references", "description", "info"]
    bs_pop_keys = ["info", "provenance", "_id", "followup_time", "followup_state", "cohorts", "icdo_morphology", "icdo_topography"]

    pxf_resources = _phenopack_resources(byc)
    server = select_this_server( byc )

    bios_s = data_db["biosamples"].find({"individual_id":ind["id"]})

    for bios in bios_s:

        bios.update({
            "files": [
                {
                    "uri": "{}/beacon/biosamples/{}/variants/?output=vcf".format(server, bios["id"]),
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

    if not isinstance(this_object, dict):
        return this_object

    for k in list(this_object.keys()):
        if isinstance(this_object[k], dict):
            if not this_object[k]:
                this_object.pop(k, None)
        elif isinstance(this_object[k], list):
            if len(this_object[k]) < 1:
                this_object.pop(k, None)

    return this_object

################################################################################

def individual_remap_pgx_diseases(ind):

    #TODO: This should be more general, i.e. what is mapped/how, deleted...

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

def _phenopack_resources(byc):

    # TODO: make this general, at least for phenopacket response, and only scan used prefixes

    f_d = byc["filter_definitions"]
    # rkeys = ["NCITgrade", "NCITstage", "NCITtnm", "NCIT", "PATOsex", "EFOfus" ]
    rkeys = ["NCIT", "PATOsex", "EFOfus", "UBERON" ]

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
        if type(br_r) is not "dict":
            continue
        r_s_res[br_i].pop("_id", None)
        clean_empty_fields(r_s_res[br_i])

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

    for i_k in ["start", "end"]:
        v.update({ i_k: int( v[i_k] ) })

    for d_f in drop_fields:   
        v.pop(d_f, None)

    return v


