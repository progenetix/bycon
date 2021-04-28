from cytoband_utils import *

################################################################################
################################################################################
################################################################################

def generate_genomic_intervals(byc, genome_binning="1Mb"):

    if not "cytobands" in byc:
        parse_cytoband_file(byc)

    chro_maxes = {}
    for cb in byc["cytobands"]:               # assumes the bands are sorted
        chro_maxes.update({ cb["chro"]: int(cb["end"])})

    byc["genomic_intervals"] = []
    i = 0

    if genome_binning == "cytobands":
        for cb in byc["cytobands"]:
            byc["genomic_intervals"].append( {
                    "index": int(cb["i"]),
                    "reference_name": cb["chro"],
                    "start": int(cb["start"]),
                    "end": int(cb["end"]),
                    "size": int(cb["end"]) - int(cb[ "start"])
                })
        return byc

    # otherwise intervals

    if not genome_binning in byc["interval_definitions"]:
        genome_binning = "default"

    int_b = byc["interval_definitions"]["genome_binning"][genome_binning]

    for chro in chro_maxes:
        start = 0
        end = start + int_b
        while start <= chro_maxes[chro]:
            if end > chro_maxes[chro]:
                end = chro_maxes[chro]
            byc["genomic_intervals"].append( {
                    "index": i,
                    "reference_name": chro,
                    "start": start,
                    "end": end,
                    "size": end - start
                })
            start += int_b
            end += int_b
            i += 1

    genome_size = 0
    for chro in chro_maxes:
        genome_size += chro_maxes[chro]

    byc.update({"genome_size": genome_size})

    return byc

################################################################################
       
def interval_cnv_frequencies(cnvmaps, byc):

    int_cov_labs = { "DUP": 'dupcoverage', "DEL": 'delcoverage' }
    int_f_labs = { "DUP": 'dupfrequencies', "DEL": 'delfrequencies' }

    int_no = len(byc["genomic_intervals"])

    maps = {
        "intervals": int_no,
        "binning": byc["genome_binning"],
        "frequencymaps": { }
    }

    fFactor = 100;
    if len(cnvmaps) > 1:
        fFactor = 100 / len(cnvmaps)

    min_f = byc["interval_definitions"]["interval_min_fraction"]

    for cnv_type, cnv_lab in int_cov_labs.items():

        f_label = int_f_labs[ cnv_type ]

        maps.update({ f_label: [ ] })

        for i, interval in enumerate(byc["genomic_intervals"]):
            m_count = 0
            for m in cnvmaps:
                if float(m[ cnv_lab ][i]) >= min_f:
                    m_count += 1

            f = round(fFactor * m_count, 3)
            maps[ f_label ].append( f )

    return maps

################################################################################

def interval_cnv_maps(variants, byc):

    int_cov_labs = { "DUP": 'dupcoverage', "DEL": 'delcoverage' }
    int_val_labs = { "DUP": 'dupmax', "DEL": 'delmin' }

    int_no = len(byc["genomic_intervals"])

    maps = {
        "intervals": int_no,
        "binning": byc["genome_binning"]
    }

    cnv_stats = {
        "cnvcoverage": 0,
        "dupcoverage": 0,
        "delcoverage": 0,
        "cnvfraction": 0,
        "dupfraction": 0,
        "delfraction": 0
    }

    for cov_lab in int_cov_labs.values():
        maps.update( { cov_lab: [ 0 for i in range(int_no) ] } )
    for val_lab in int_val_labs.values():
        maps.update( { val_lab: [ 0 for i in range(int_no) ] } )

    if len(variants) < 1:
        return maps, cnv_stats

    # the values_map collects all values for the given interval to retrieve
    # the min and max values of each interval
    values_map = [  [ ] for i in range(int_no) ]

    for v in variants:

        if not "variant_type" in v:
            continue
        if not v["variant_type"] in int_cov_labs.keys():
            continue

        for i, interval in enumerate(byc["genomic_intervals"]):

            if _has_overlap(interval, v):

                ov_end = min(interval["end"], v["end"])
                ov_start = max(interval["start"], v["start"])
                ov = ov_end - ov_start

                maps[ int_cov_labs[ v["variant_type"] ] ][ i ] += ov

                try:
                    # print(type(v["info"]["cnv_value"]))
                    if type(v["info"]["cnv_value"]) == int or type(v["info"]["cnv_value"]) == float:
                        values_map[ i ].append(v["info"]["cnv_value"])
                except:
                    pass

    # statistics
    for lab in int_cov_labs.values():
        for i, interval in enumerate(byc["genomic_intervals"]):
            if maps[ lab ][ i ] > 0:
                cnv_stats[ lab ] += maps[ lab ][ i ]
                cnv_stats[ "cnvcoverage" ] += maps[ lab ][ i ]
                maps[ lab ][ i ] = round( maps[ lab ][ i ] / byc["genomic_intervals"][ i ]["size"], 4 )

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
                maps["dupmax"][ i ] = round(values_map[ i ][-1], 3)
            if values_map[ i ][0] < 0:
                maps["delmin"][ i ] = round(values_map[ i ][0], 3)

    return maps, cnv_stats


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
