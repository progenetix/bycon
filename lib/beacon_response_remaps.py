import datetime, re
from pymongo import MongoClient

################################################################################

def reshape_resultset_results(ds_id, r_s_res, byc):

    r_s_res = remap_variants(r_s_res, byc)
    r_s_res = remap_analyses(r_s_res, byc)
    r_s_res = remap_biosamples(r_s_res, byc)
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
    if not "variant" in byc["response_type"]:
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

def de_vrsify_variant(v, byc):

    v_d = byc["variant_definitions"]

    v_r =  {
        "id": v["id"],
        "variant_internal_id": v.get("variant_internal_id", None),
        "callset_id": v.get("callset_id", None),
        "biosample_id": v.get("biosample_id", None),
        "reference_bases": v.get("reference_bases", None),
        "alternate_bases": v.get("alternate_bases", None),
        "reference_name": v_d["refseq_chronames"][ v["location"]["sequence_id"] ],
        "start": v["location"]["interval"]["start"]["value"],
        "end": v["location"]["interval"]["end"]["value"],
        "info": v.get("info", {})
    }

    if "variant_state" in v:
        efo = v["variant_state"].get("id", None)
        try:
            v_r.update({"variant_type": v_d["efo_vrs_map"][ efo ]["DUPDEL"] })
        except:
            pass

    return v_r

################################################################################

def vrsify_variant(v, v_d):

    t = v.get("type", None)
    v_t = v.get("variant_type", None)
    a_b = v.get("alternate_bases", None)

    if t is None:
        if a_b is not None:
            t = "Allele"
        elif v_t in ["DUP", "AMP", "DEL", "HOMODEL"]:
            t = "RelativeCopyNumber"

    if "Allele" in t:
        return vrsify_snv(v, v_d)
    else:
        return vrsify_cnv(v, v_d)

################################################################################

def vrsify_cnv(v, v_d):

    v_t = v.get("type", "RelativeCopyNumber")
    ref_id = refseq_from_chro(v["reference_name"], v_d)
    start_v = int(v["start"])
    end_v = int( v.get("end",start_v + 1 ) )

    vrs_class = None
    if "variant_state" in v:
        vrs_class = efo_to_vrs_class(v["variant_state"].get("id", None), v_d)

    vrs_v = {
                "type": v_t,
                "relative_copy_class": vrs_class,
                "location":{
                    "sequence_id": ref_id,
                    "type": "SequenceLocation",
                    "interval": {
                        "start": {
                            "type": "Number",
                            "value": start_v
                        },
                        "end": {
                            "type": "Number",
                            "value": end_v
                        }
                    }
                }
            }

    return vrs_v

################################################################################

def vrsify_snv(v, v_d):

    v_t = v.get("type", "Allele")
    ref_id = refseq_from_chro(v["reference_name"], v_d)
    alt = v.get("alternate_bases", None)

    if alt is None:
        return {}

    ref_l = int(len(v.get("reference_bases", "")))
    alt_l = int(len(v.get("alternate_bases", "")))
    l = alt_l - ref_l + 1

    ref_id = refseq_from_chro(v["reference_name"], v_d)
    start_v = int(v["start"])
    end_v = int( start_v + l )

    vrs_v = {
                "type": v_t,
                "state": {
                    "type": "LiteralSequenceExpression",
                    "sequence": alt
                },
                "location":{
                    "sequence_id": ref_id,
                    "type": "SequenceLocation",
                    "interval": {
                        "type": "SequenceInterval",
                        "start": {
                            "type": "Number",
                            "value": start_v
                        },
                        "end": {
                            "type": "Number",
                            "value": end_v
                        }
                    }
                }
            }

    return vrs_v

################################################################################

def efo_to_vrs_class(efo_id, v_d):
    
    efo_vrs = v_d["efo_vrs_map"]
    if efo_id in efo_vrs:
        return efo_vrs[ efo_id ]["relative_copy_class"]

    return None

################################################################################

def refseq_from_chro(chro, v_d):

    chro = re.sub("chr", "", chro) # just making sure ...

    if not chro in v_d["chro_refseq_ids"]:
        return chro

    return v_d["chro_refseq_ids"][ chro ]

################################################################################

def remap_analyses(r_s_res, byc):

    if not "analysis" in byc["response_type"]:
        return r_s_res

    for cs_i, cs_r in enumerate(r_s_res):
        # TODO: REMOVE VERIFIER HACKS
        r_s_res[cs_i].update({"pipeline_name": "progenetix", "analysis_date": "1967-11-11" })
        try:
            r_s_res[cs_i].pop("cnv_statusmaps")
        except:
            pass

    return r_s_res

################################################################################

def remap_runs(r_s_res, byc):

    if not "run" in byc["response_type"]:
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

    if not "biosample" in byc["response_type"]:
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

    if not "individual" in byc["response_type"]:
        return r_s_res



    return r_s_res

################################################################################

def remap_phenopackets(ds_id, r_s_res, byc):

    if not "phenopacket" in byc["response_type"]:
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

    pxf_bios = []

    pxf_resources = _phenopack_resources(byc)

    bios_s = data_db["biosamples"].find({"individual_id":ind["id"]})

    for bios in bios_s:
        for k in ["info", "provenance", "_id"]:
            bios.pop(k, None)
        pxf_bios.append(bios)

    del_keys = ["_id"]

    for k in del_keys:
        ind.pop(k, None)

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
