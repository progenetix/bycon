import pymongo

from cgi_parsing import *
from datatable_utils import get_nested_value
from query_generation import paginate_list
from response_remapping import de_vrsify_variant, normalize_variant_values_for_export


################################################################################

def export_variants_download(ds_id, byc):

    data_client = pymongo.MongoClient()
    v_coll = data_client[ ds_id ][ "variants" ]
    ds_results = byc["dataset_results"][ds_id]
 
    v__ids = byc["dataset_results"][ds_id]["variants._id"].get("target_values", [])
    if test_truthy( byc["form_data"].get("paginate_results", True) ):
        v__ids = paginate_list(v__ids, byc)

    open_json_streaming(byc, "variants.json")

    for v_id in v__ids[:-1]:
        v = v_coll.find_one( { "_id": v_id }, { "_id": 0 } )
        print(decamelize_words(json.dumps(camelize(v), indent=None, sort_keys=False, default=str, separators=(',', ':')), end = ','))
    v = v_coll.find_one( { "_id": v__ids[-1]}, { "_id": 0 }  )
    print(decamelize_words(json.dumps(camelize(v), indent=None, sort_keys=False, default=str, separators=(',', ':')), end = ''))

    close_json_streaming()


################################################################################

def stream_pgx_meta_header(ds_id, ds_results, byc):

    if not "pgxseg" in byc["output"] and not "pgxmatrix" in byc["output"]:
        return

    s_r_rs = byc["service_response"]["response"]["result_sets"][0]
    b_p = byc["pagination"]

    mongo_client = pymongo.MongoClient()
    bs_coll = mongo_client[ ds_id ][ "biosamples" ]

    open_text_streaming(byc["env"])

    for d in ["id", "assemblyId"]:
        print("#meta=>{}={}".format(d, byc["dataset_definitions"][ds_id][d]))
    for k, n in s_r_rs["info"]["counts"].items():
        print("#meta=>{}={}".format(k, n))
    print("#meta=>pagination.skip={};pagination.limit={};pagination.range={},{}".format(b_p["skip"], b_p["skip"], b_p["range"][0] + 1, b_p["range"][1]))
            
    print_filters_meta_line(byc)

    for bs_id in ds_results["biosamples.id"][ "target_values" ]:
        bs = bs_coll.find_one( { "id": bs_id } )
        if not bs:
            continue
        h_line = pgxseg_biosample_meta_line(byc, bs, "histological_diagnosis_id")
        print(h_line)

    return


################################################################################

def pgxseg_biosample_meta_line(byc, biosample, group_id_key="histological_diagnosis_id"):

    dt_m = byc["datatable_mappings"]
    io_params = dt_m["entities"][ "biosample" ]["parameters"]

    g_id_k = group_id_key
    g_lab_k = re.sub("_id", "_label", g_id_k)

    line = [ "#sample=>id={}".format(biosample.get("id", "¡¡¡NONE!!!")) ]

    for par, par_defs in io_params.items():

        in_pgxseg = par_defs.get("compact", False)
        if in_pgxseg is False:
            continue

        parameter_type = par_defs.get("type", "string")
        pres = par_defs.get("prefix_split", {})

        if len(pres.keys()) < 1:
            db_key = par_defs.get("db_key", "___undefined___")
            v = get_nested_value(biosample, db_key)
            h_v = ""
            if isinstance(v, list):
                h_v = "::".join(map(str, (v)))
            else:
                h_v = str(v)

            if len(h_v) > 0:
                if g_id_k == par:
                    line.append("group_id={}".format(h_v))
                if g_lab_k == par:
                    line.append("group_label={}".format(h_v))
                line.append("{}={}".format(par, h_v))
        else:

            par_vals = biosample.get(par, [])
            if not isinstance(par_vals, list):
                continue
            for pre, pre_defs in pres.items():
                in_pgxseg = pre_defs.get("compact", False)
                if in_pgxseg is False:
                    continue
                for v in par_vals:
                    if v.get("id", "___none___").startswith(pre):
                        line.append("{}_id___{}={}".format(par, pre, v.get("id")))
                        l = v.get("label", "")
                        if len(l) > 0:
                            line.append("{}_label___{}={}".format(par, pre, v.get("id")))
                        continue

    h_line = ";".join(line)

    return h_line

################################################################################    

def __pgxmatrix_interval_header(info_columns, byc):

    int_line = info_columns.copy()

    for iv in byc["genomic_intervals"]:
        int_line.append("{}:{}-{}:DUP".format(iv["reference_name"], iv["start"], iv["end"]))
    for iv in byc["genomic_intervals"]:
        int_line.append("{}:{}-{}:DEL".format(iv["reference_name"], iv["start"], iv["end"]))

    return int_line


################################################################################

def print_filters_meta_line(byc):

    if "filters" in byc["service_response"]["meta"]["received_request_summary"]:
        f_vs = []
        for f in byc["service_response"]["meta"]["received_request_summary"]["filters"]:
            f_vs.append(f["id"])
        print("#meta=>filters="+','.join(f_vs))

    return

################################################################################

def export_pgxseg_download(ds_id, byc):

    data_client = pymongo.MongoClient()
    v_coll = data_client[ ds_id ][ "variants" ]
    ds_results = byc["dataset_results"][ds_id]
    v__ids = byc["dataset_results"][ds_id]["variants._id"].get("target_values", [])
    if test_truthy( byc["form_data"].get("paginate_results", True) ):
        v__ids = paginate_list(v__ids, byc)

    stream_pgx_meta_header(ds_id, ds_results, byc)
    print_pgxseg_header_line()

    for v_id in v__ids:
        v = v_coll.find_one( { "_id": v_id} )
        print_variant_pgxseg(v, byc)

    close_text_streaming()

################################################################################

def print_variant_pgxseg(v, byc):

    print( pgxseg_variant_line(v, byc) )

################################################################################

def print_pgxseg_header_line():

    print( pgxseg_header_line() )

################################################################################

def pgxseg_header_line():

    return "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format("biosample_id", "reference_name", "start", "end", "log2", "variant_type", "reference_bases", "alternate_bases" )

################################################################################

def pgxseg_variant_line(v, byc):

    v = de_vrsify_variant(v, byc)
    if v is False:
        return v

    v["log2"] = v["info"].get("log2", ".")

    return "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(v["biosample_id"], v["reference_name"], v["start"], v["end"], v["log2"], v["variant_type"], v["reference_bases"], v["alternate_bases"])

################################################################################

def export_callsets_matrix(ds_id, byc):

    m_format = "coverage"
    if "val" in byc["output"]:
        m_format = "values"

    ds_results = byc["dataset_results"][ds_id]
    p_r = byc["pagination"]

    if not "callsets._id" in ds_results:
        return

    cs_r = ds_results["callsets._id"]

    mongo_client = pymongo.MongoClient()
    bs_coll = mongo_client[ ds_id ][ "biosamples" ]
    cs_coll = mongo_client[ ds_id ][ "callsets" ]

    open_text_streaming(byc["env"], "interval_callset_matrix.pgxmatrix")

    for d in ["id", "assemblyId"]:
        print("#meta=>{}={}".format(d, byc["dataset_definitions"][ds_id][d]))
    print_filters_meta_line(byc)
    print("#meta=>data_format=interval_"+m_format)

    info_columns = [ "analysis_id", "biosample_id", "group_id" ]
    h_line = __pgxmatrix_interval_header(info_columns, byc)
    print("#meta=>genome_binning={};interval_number={}".format(byc["genome_binning"], len(byc["genomic_intervals"])) )
    print("#meta=>no_info_columns={};no_interval_columns={}".format(len(info_columns), len(h_line) - len(info_columns)))

    q_vals = cs_r["target_values"]
    r_no = len(q_vals)
    if r_no > p_r["limit"]:
        if test_truthy( byc["form_data"].get("paginate_results", True) ):
            q_vals = paginate_list(q_vals, byc)
        print('#meta=>"WARNING: Only analyses {} - {} (from {}) will be included pagination skip and limit"'.format((p_r["range"][0] + 1), p_r["range"][-1], cs_r["target_count"]))

    bios_ids = set()
    cs_ids = {}
    cs_cursor = cs_coll.find({"_id": {"$in": q_vals } } )
    for cs in cs_cursor:
        bios = bs_coll.find_one( { "id": cs["biosample_id"] } )
        bios_ids.add(bios["id"])
        s_line = "#sample=>biosample_id={};analysis_id={}".format(bios["id"], cs["id"])
        h_d = bios["histological_diagnosis"]
        cs_ids.update({cs["id"]: h_d.get("id", "NA")})
        s_line = '{};group_id={};group_label={};NCIT::id={};NCIT::label={}'.format(s_line, h_d.get("id", "NA"), h_d.get("label", "NA"), h_d.get("id", "NA"), h_d.get("label", "NA"))
        print(s_line)

    print("#meta=>biosampleCount={};analysisCount={}".format(len(bios_ids), cs_r["target_count"]))
    print("\t".join(h_line))

    for cs_id, group_id in cs_ids.items():
        cs = cs_coll.find_one({"id":cs_id})
        if "values" in m_format:
            print("\t".join(
                [
                    cs_id,
                    cs.get("biosample_id", "NA"),
                    group_id,
                    *map(str, cs["cnv_statusmaps"]["max"]),
                    *map(str, cs["cnv_statusmaps"]["min"])
                ]
            ))
        else:
            print("\t".join(
                [
                    cs_id,
                    cs.get("biosample_id", "NA"),
                    group_id,
                    *map(str, cs["cnv_statusmaps"]["dup"]),
                    *map(str, cs["cnv_statusmaps"]["del"])
                ]
            ))

    close_text_streaming()

################################################################################

def export_pgxseg_frequencies(byc, results):

    if not "pgxseg" in byc["output"] and not "pgxfreq" in byc["output"]:
        return

    open_text_streaming(byc["env"], "interval_frequencies.pgxfreq")

    print("#meta=>genome_binning={};interval_number={}".format(byc["genome_binning"], len(byc["genomic_intervals"])) )
    h_ks = ["reference_name", "start", "end", "gain_frequency", "loss_frequency", "no"]

    # should get error checking if made callable

    for f_set in results:
        m_line = []
        for k in ["group_id", "label", "dataset_id", "sample_count"]:
            m_line.append(k+"="+str(f_set[k]))
        print("#group=>"+';'.join(m_line))

    print("group_id\t"+"\t".join(h_ks))

    for f_set in results:
        for intv in f_set["interval_frequencies"]:
            v_line = [ ]
            v_line.append(f_set[ "group_id" ])
            for k in h_ks:
                v_line.append(str(intv[k]))
            print("\t".join(v_line))

    close_text_streaming()

################################################################################

def export_pgxmatrix_frequencies(byc, results):

    open_text_streaming(byc["env"], "interval_frequencies.pgxmatrix")

    print("#meta=>genome_binning={};interval_number={}".format(byc["genome_binning"], len(byc["genomic_intervals"])) )

    # should get error checking if made callable
    for f_set in results:
        m_line = []
        for k in ["group_id", "label", "dataset_id", "sample_count"]:
            m_line.append(k+"="+str(f_set[k]))
        print("#group=>"+';'.join(m_line))
    # header

    h_line = [ "group_id" ]
    h_line = __pgxmatrix_interval_header(h_line, byc)
    print("\t".join(h_line))

    for f_set in results:
        f_line = [ f_set[ "group_id" ] ]
        for intv in f_set["interval_frequencies"]:
            f_line.append( str(intv["gain_frequency"]) )
        for intv in f_set["interval_frequencies"]:
            f_line.append( str(intv["loss_frequency"]) )

        print("\t".join(f_line))

    close_text_streaming()

