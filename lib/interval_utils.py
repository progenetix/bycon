import statistics
from progress.bar import Bar
import numpy as np

from cytoband_utils import *

################################################################################
################################################################################
################################################################################

def generate_genomic_intervals(byc, genome_binning="1Mb"):

    if not "cytobands" in byc:
        parse_cytoband_file(byc)

    c_l = byc["cytolimits"]
    i_d = byc["interval_definitions"]

    # cytobands ################################################################
    
    byc["cytoband_intervals"] = []
    for cb in byc["cytobands"]:
        byc["cytoband_intervals"].append( {
                "no": int(cb["i"]),
                "id": "{}:{}-{}".format(cb["chro"], cb["start"], cb["end"]),
                "reference_name": cb["chro"],
                "start": int(cb["start"]),
                "end": int(cb["end"]),
                "size": int(cb["end"]) - int(cb[ "start"])
            })

    if genome_binning == "cytobands":
        byc.update({"genomic_intervals": byc["cytoband_intervals"].copy() })
        return byc

    # otherwise intervals ######################################################

    if not genome_binning in i_d:
        genome_binning = "default"

    int_b = i_d["genome_binning"][genome_binning]
    e_p = i_d["terminal_intervals_soft_expansion"]

    byc["genomic_intervals"] = []
    i = 1

    for chro in c_l:

        p_max = c_l[chro]["p"][-1]
        q_max = c_l[chro]["size"]
        arm = "p"
        start = 0

        # calculate first interval to end p-arm with a full sized one
        p_first = p_max
        while p_first >= int_b + e_p:
            p_first -= int_b

        end = start + p_first
        while start < q_max:
            int_p = int_b
            if end > q_max:
                end = q_max
            elif q_max < end + e_p:
                end = q_max
                int_p += e_p
            if end >= p_max:
                arm = "q"
            size = end - start
            byc["genomic_intervals"].append( {
                    "no": i,
                    "id": "{}{}:{}-{}".format(chro, arm, start, end),
                    "reference_name": chro,
                    "arm": arm,
                    "start": start,
                    "end": end,
                    "size": size
                })
            # if size > 1000000:
            #     print("{}{}:{}-{}\t{}".format(chro, arm, start, end, size))
            start = end
            end += int_p
            i += 1

    return byc

################################################################################

def interval_cnv_arrays(v_coll, query, byc):

    cov_labs = { "DUP": 'dup', "DEL": 'del' }
    val_labs = { "DUP": 'max', "DEL": 'min' }
    cnv_val_defaults = { "DUP": 0.58, "DEL": -1 }

    int_no = len(byc["genomic_intervals"])
    proto = [0 for i in range(int_no)] 

    maps = {
        "interval_count": int_no,
        "binning": byc["genome_binning"]
    }

    for cov_lab in cov_labs.values():
        maps.update({cov_lab: proto.copy()})
    for val_lab in val_labs.values():
        maps.update({val_lab: proto.copy()})

    cnv_stats = {
        "cnvcoverage": 0,
        "dupcoverage": 0,
        "delcoverage": 0,
        "cnvfraction": 0,
        "dupfraction": 0,
        "delfraction": 0,
        "chrofractions": {}
    }

    v_no = v_coll.count_documents( query )

    if v_no < 1:
        return maps, cnv_stats

    # the values_map collects all values for the given interval to retrieve
    # the min and max values of each interval
    values_map = [  [ ] for i in range(int_no) ]

    for v in v_coll.find( query ):

        # print("Variant: {} <=> {}".format(v["callset_id"], v["biosample_id"]))

        if not "variant_type" in v:
            continue
        if not v["variant_type"] in cov_labs.keys():
            continue

        cov_lab = cov_labs[ v["variant_type"] ]

        for i, interval in enumerate(byc["genomic_intervals"]):

            if _has_overlap(interval, v):

                ov_end = min(interval["end"], v["end"])
                ov_start = max(interval["start"], v["start"])
                ov = ov_end - ov_start

                maps[ cov_lab ][i] += ov

                try:
                    # print(type(v["info"]["cnv_value"]))
                    if type(v["info"]["cnv_value"]) == int or type(v["info"]["cnv_value"]) == float:
                        values_map[ i ].append(v["info"]["cnv_value"])
                    else:
                        values_map[ i ].append(cnv_val_defaults[ v["variant_type"] ])
                except:
                    pass

    # statistics
    for cov_lab in cov_labs.values():
        for i, interval in enumerate(byc["genomic_intervals"]):
            if maps[cov_lab][i] > 0:
                cnv_stats[ cov_lab+"coverage" ] += maps[cov_lab][i]
                cnv_stats[ "cnvcoverage" ] += maps[cov_lab][i]
                maps[cov_lab][i] = round( maps[cov_lab][i] / byc["genomic_intervals"][ i ]["size"], 3 )

    for s_k in cnv_stats.keys():
        if "coverage" in s_k:
            f_k = re.sub("coverage", "fraction", s_k)
            cnv_stats.update({s_k: int(cnv_stats[ s_k ]) })
            cnv_stats.update({f_k: round(cnv_stats[ s_k ] / byc["genome_size"] , 3) })
            if cnv_stats[f_k] > 1:
                print("!!! {} => {}: {}".format(v["callset_id"], f_k, cnv_stats[f_k]))

    # the values for each interval are sorted, to allow extracting the min/max 
    # values by position
    # the last of the sorted values is assigned iF > 0
    for i in range(len(values_map)):
        if values_map[ i ]:
            values_map[ i ].sort()
            if values_map[ i ][-1] > 0:
                maps["max"][i] = round(values_map[ i ][-1], 3)
            if values_map[ i ][0] < 0:
                maps["min"][i] = round(values_map[ i ][0], 3)

    return maps, cnv_stats

################################################################################

def interval_counts_from_callsets(callsets, byc):

    """
    This method will analyze a set (either list or MongoDB Cursor) of Progenetix
    callsets with CNV statusmaps and return a list of standard genomic interval
    objects with added per-interval quantitative data.
    """

    min_f = byc["interval_definitions"]["interval_min_fraction"]
    int_fs = byc["genomic_intervals"].copy()
    int_no = len(int_fs)

    # callsets can be either a list or a MongoDB Cursor (which has to be re-set)
    if type(callsets).__name__ == "Cursor":
        callsets.rewind()

    cs_no = len(list(callsets))
    fFactor = 0

    if cs_no > 0:
        fFactor = 100 / cs_no;

    pars = {
        "gain": {"cov_l": "dup", "val_l": "max" },
        "loss": {"cov_l": "del", "val_l": "min" }
    }

    for t in pars.keys():

        covs = np.zeros( (cs_no, int_no) )
        vals = np.zeros( (cs_no, int_no) )

        if type(callsets).__name__ == "Cursor":
            callsets.rewind()

        for i, cs in enumerate(callsets):
            covs[i] = cs["info"]["statusmaps"][ pars[t]["cov_l"] ]
            vals[i] = cs["info"]["statusmaps"][ pars[t]["val_l"] ]

        counts = np.count_nonzero(covs >= min_f, axis=0)
        frequencies = np.around(counts * fFactor, 3)
        medians = np.around(np.ma.median(np.ma.masked_where(covs < min_f, vals), axis=0).filled(0), 3)
        means = np.around(np.ma.mean(np.ma.masked_where(covs < min_f, vals), axis=0).filled(0), 3)

        for i, interval in enumerate(int_fs):
            int_fs[i].update( {
                t+"_frequency": frequencies[i],
                t+"_median": medians[i],
                t+"_mean": means[i]
            } )

    return int_fs

################################################################################

def _has_overlap(interval, v):

    if not interval["reference_name"] == v["reference_name"]:
        return False

    if not interval["end"] > v["start"]:
        return False

    if not interval["start"] < v["end"]:
        return False

    return True

################################################################################
