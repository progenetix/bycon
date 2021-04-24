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
                    "chro": cb["chro"],
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
                    "chro": chro,
                    "start": start,
                    "end": end,
                    "size": end - start
                })
            start += int_b
            end += int_b
            i += 1

    return byc
