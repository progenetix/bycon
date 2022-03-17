import datetime, re

################################################################################

def remap_variants(r_s_res, byc):

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

        v_p = d_vs[0]

        variation = vrsify_variant(v_p, v_d)
        # TODO: This default variant_type assignment may break at some point...
        v_t = v_p.get("variant_type", "SNV")

        vrs_class = None
        if "variant_state" in v_p:
            vrs_class = efo_to_vrs_class(v_p["variant_state"].get("id", None), v_d)

        v = {
            "variant_internal_id": d,
            "variant_type": v_t,
            "variant_state": vrs_class,
            "variation": variation,
            "case_level_data": []
        }

        for v_v in ["reference_bases", "alternate_bases"]:
            b = v_p.get(v_v, "")
            if len(b) > 0:
                v.update({ v_v: b })

        for d_v in d_vs:
            v["case_level_data"].append(
                {   
                    "id": d_v["id"],
                    "biosample_id": d_v["biosample_id"],
                    "analysis_id": d_v["callset_id"]
                }
            )

        variants.append(v)

    return variants

################################################################################

def vrsify_variant(v, v_d):

    v_t = v.get("variant_type", "SNV")
    if "SNV" in v_t:
        return vrsify_snv(v, v_d)
    else:
        return vrsify_cnv(v, v_d)

################################################################################

def vrsify_cnv(v, v_d):

    v_t = v.get("variant_type", "CNV")
    ref_id = refseq_from_chro(v["reference_name"], v_d)
    start_v = int(v["start"])
    end_v = int( v.get("end",start_v + 1 ) )

    vrs_class = None
    if "variant_state" in v:
        vrs_class = efo_to_vrs_class(v["variant_state"].get("id", None), v_d)

    vrs_v = {
                "type": "RelativeCopyNumber",
                "relative_copy_class": vrs_class,
                "subject": {
                    "type": "DerivedSequenceExpression",
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
            }

    return vrs_v

################################################################################

def vrsify_snv(v, v_d):

    ref_id = refseq_from_chro(v["reference_name"], v_d)
    alt = v.get("alternate_bases", None)

    if alt is None:
        return {}

    ref_id = refseq_from_chro(v["reference_name"], v_d)
    start_v = int(v["start"])
    end_v = int( v.get("end",start_v + len(alt) ) )

    vrs_v = {
                "type": "Allele",
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
        return efo_vrs[ efo_id ]["vrs"]

    return None

################################################################################

def refseq_from_chro(chro, v_d):

    chro = re.sub("chr", "", chro) # just making sure ...

    if not chro in v_d["chro_refseq_ids"]:
        return chro

    return "refseq:" + v_d["chro_refseq_ids"][ chro ]

################################################################################

def remap_analyses(r_s_res, byc):

    # TODO: REMOVE VERIFIER HACKS
    if not "analysis" in byc["response_type"]:
        return r_s_res

    for cs_i, cs_r in enumerate(r_s_res):
        r_s_res[cs_i].update({"pipeline_name": "progenetix", "analysis_date": "1967-11-11" })
        try:
            r_s_res[cs_i].pop("cnv_statusmaps")
        except:
            pass

    return r_s_res

################################################################################

def remap_runs(r_s_res, byc):

    # TODO: REMOVE VERIFIER HACKS
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

    # TODO: REMOVE VERIFIER HACKS
    if not "biosample" in byc["response_type"]:
        return r_s_res

    for bs_i, bs_r in enumerate(r_s_res):
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

def remap_all(r_s_res):

    for br_i, br_r in enumerate(r_s_res):
        r_s_res[br_i].pop("_id", None)
        r_s_res[br_i].pop("description", None)

    return r_s_res
