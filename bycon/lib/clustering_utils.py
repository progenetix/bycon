import scipy.cluster

################################################################################

def cluster_frequencies(plv, byc):

    m = plv.get("plot_cluster_metric", "complete")

    matrix = matrix_from_interval_frequencies(plv, byc)
    linkage = scipy.cluster.hierarchy.linkage(matrix, method=m)
    dendrogram = scipy.cluster.hierarchy.dendrogram(linkage, no_plot=True, orientation="right")
    
    return dendrogram

################################################################################

def matrix_from_interval_frequencies(plv, byc):

    matrix = []

    for f_set in plv["results"]:

        i_f = f_set.get("interval_frequencies", [])
        if_line = []

        for i_f in f_set.get("interval_frequencies", []):
            if_line.append( i_f.get("gain_frequency", 0) )
        for i_f in f_set.get("interval_frequencies", []):
            if_line.append( i_f.get("loss_frequency", 0) )

        matrix.append(if_line)

    return matrix

################################################################################

def cluster_samples(plv, byc):

    m = plv.get("plot_cluster_metric", "complete")

    matrix = []

    for s in plv["results"]:
        s_line = []

        if "intcoverage" in plv.get("plot_samples_cluster_type", ""):

            c_m = s.get("cnv_statusmaps", {})
            dup_l = c_m.get("dup", [])
            del_l = c_m.get("del", [])
            for i_dup in dup_l:
                s_line.append(i_dup)
            for i_del in del_l:
                s_line.append(i_del)
        else:
            c_s = s.get("cnv_chro_stats", {})
            for c_a, c_s_v in c_s.items():
                s_line.append(c_s_v.get("dupfraction", 0))
            for c_a, c_s_v in c_s.items():
                s_line.append(c_s_v.get("delfraction", 0))

        matrix.append(s_line)

    linkage = scipy.cluster.hierarchy.linkage(matrix, method=m)
    reorder = scipy.cluster.hierarchy.leaves_list(linkage)
    dendrogram = scipy.cluster.hierarchy.dendrogram(linkage, no_plot=True, orientation="right")

    return dendrogram
