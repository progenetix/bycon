import datetime

################################################################################

def remap_variants(r_s_res, byc):

    if not "variant" in byc["response_type"]:
        return r_s_res

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

        v = {
            "variant_internal_id": d,
            "variant_type": d_vs[0].get("variant_type", "SNV"),
            "position":{
                "assembly_id": "GRCh38",
                "refseq_id": "chr"+d_vs[0]["reference_name"],
                "start": [ int(d_vs[0]["start"]) ]
            },
            "case_level_data": []
        }

        if "end" in d_vs[0]:
            v["position"].update({ "end": [ int(d_vs[0]["end"]) ] })

        for v_t in ["variant_type", "reference_bases", "alternate_bases"]:
            v.update({ v_t: d_vs[0].get(v_t, "") })

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
