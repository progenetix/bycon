import scipy.cluster

################################################################################
################################################################################
################################################################################

class ByconCluster():
    def __init__(self, plv):
        self.plv = plv
        self.data = plv.get("results", [])
        self.cluster_metric = plv.get("plot_cluster_metric", "complete")
        self.samples_cluster_type = plv.get("plot_samples_cluster_type", "")
        self.tree_side = "right"
        self.matrix = []
        self.dendrogram = {}
        self.new_order = []


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def cluster_frequencies(self):
        self.__matrix_from_interval_frequencies()
        self.__make_dendrogram()
        return self.dendrogram


    # -------------------------------------------------------------------------#

    def cluster_samples(self):
        self.__matrix_from_samples()
        self.__make_dendrogram()
        return self.dendrogram
    

    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __matrix_from_interval_frequencies(self):
        for f_set in self.data:
            i_f = f_set.get("interval_frequencies", [])
            if_line = []
            for i_f in f_set.get("interval_frequencies", []):
                if_line.append( i_f.get("gain_frequency", 0) )
            for i_f in f_set.get("interval_frequencies", []):
                if_line.append( i_f.get("loss_frequency", 0) )
            self.matrix.append(if_line)


    # -------------------------------------------------------------------------#

    def __matrix_from_samples(self):
        for s in self.data:
            s_line = []
            if "intcoverage" in self.samples_cluster_type:
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
            self.matrix.append(s_line)


    # -------------------------------------------------------------------------#

    def __make_dendrogram(self):
        linkage = scipy.cluster.hierarchy.linkage(self.matrix, method=self.cluster_metric)
        self.new_order = scipy.cluster.hierarchy.leaves_list(linkage)
        self.dendrogram = scipy.cluster.hierarchy.dendrogram(linkage, no_plot=True, orientation=self.tree_side)


################################################################################
################################################################################
################################################################################
