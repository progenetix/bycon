import re, sys
import numpy as np
from copy import deepcopy
from os import path, pardir
from pymongo import MongoClient

from config import DB_MONGOHOST, BYC, BYC_PARS, ENV
from genome_utils import Cytobands
from bycon_helpers import prdbug

################################################################################

"""
TODO: add docstrings to the modules & set up parsing...

The methods here address genomic binning, the assignment of sample-specific
bin values (e.g. CNV overlap, maximum/minimum observed value in the bin...) as
well as the calculation of bin statistics.

The methods rely on the existence of cytoband files which contain information
about the individual chromosomes (size, centromere position as indicated by
the transition from p- to q-arm). The bins then can be generated directly
corresponding to the listed cytobands or (the default) by producing equally
sized bins (default 1Mb). The most distal bin of each arm then can be of a
different size.

Bin sizes are selected based on the provided key for a corresponding definition
in `interval_definitions.genome_bin_sizes` (e.g. 1Mb => 1000000).

### Interval Object Schema

```
no:
  description: counter, from 1pter -> Yqter (or whatever chromosomes are provided)
  type: integer
id:
  description: the id/label of the interval, from concatenating chromosome and base range
  type: string
reference_name:
  description: the chromosome as provided in the cytoband file
  type: string
  examples:
    - 7
    - Y
arm:
  type: string
  examples:
    - p
    - q
cytobands:
  type: string
  examples:
    - 1p12.1
start:
  description: the 0/interbase start of the interval
  type: integer
end:
  description: the 0/interbase end of the interval
  type: integer
```
"""

################################################################################
################################################################################
################################################################################

class GenomeBins:
    def __init__(self):
        self.interval_definitions = BYC.get("interval_definitions", {})
        self.variant_type_definitions = BYC.get("variant_type_definitions", {})

        CB = Cytobands()
        self.cytobands = CB.get_all_cytobands()
        self.cytolimits = CB.get_all_cytolimits()
        self.genome_size = CB.get_genome_size()

        self.binning = BYC_PARS.get("genome_binning", "1Mb")
        self.genomic_intervals = []
        self.cytoband_intervals = []

        self.interval_definitions.update({"genome_binning": self.binning})

        self.__generate_cytoband_intervals()
        self.__generate_genomic_intervals()


    #--------------------------------------------------------------------------#
    #----------------------------- public -------------------------------------#
    #--------------------------------------------------------------------------#

    def get_genome_binning(self):
        return self.binning


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def get_genome_bins(self):
        return self.genomic_intervals


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def get_genome_bin_count(self):
        return len(self.genomic_intervals)


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#
    # TODO: Not used anywhere?
    def getAnalysisCoverageMaps(self, analysis_variants=[]):
        self.__prepare_analysis_intervals()
        self.analysis_variants = analysis_variants
        self.__interval_cnv_coverage_arrays()
        return self.coverage_maps


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def getAnalysisFracMaps(self, analysis_variants=[]):
        self.__prepare_analysis_intervals()
        self.analysis_variants = analysis_variants
        self.__interval_cnv_coverage_arrays()
        self.__interval_cnv_fraction_arrays()
        return self.fraction_maps


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def getAnalysisFracMapsAndStats(self, analysis_variants=[]):
        self.__prepare_analysis_intervals()
        self.analysis_variants = analysis_variants
        self.__interval_cnv_coverage_arrays()
        self.__interval_cnv_fraction_arrays()
        self.__genome_cnv_statistics()
        return self.fraction_maps, self.cnv_stats, self.chro_stats, list(self.duplicates)

    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#
    # TODO: Not used anywhere?
    def genomeCNVstats(self, analysis_variants=[]):
        self.__prepare_analysis_intervals()
        self.analysis_variants = analysis_variants
        self.__interval_cnv_coverage_arrays()
        self.__genome_cnv_statistics()
        return self.cnv_stats


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def intervalFrequencyMaps(self, analyses=[]):
        self.analyses = analyses
        self.__interval_counts_from_analyses()
        return self.interval_frequencies, self.analyses_count


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def intervalAidFrequencyMaps(self, ds_id, analysis_ids=["___none___"]):
        data_client = MongoClient(host=DB_MONGOHOST)
        data_db = data_client[ ds_id ]
        ana_coll = data_db["analyses"]
        query = {"id": {"$in": analysis_ids}, "operation.id": "EDAM:operation_3961"}
        if ana_coll.count_documents(query) < 1:
            return {}, 0
        self.analyses = ana_coll.find(query)
        self.__interval_counts_from_analyses()
        return self.interval_frequencies, self.analyses_count


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#
    # TODO: Not used anywhere?
    def getVariantDuplicates(self, analysis_variants=[]):
        self.__prepare_analysis_intervals()
        self.analysis_variants = analysis_variants
        self.__interval_cnv_coverage_arrays()
        return list[self.duplicates]


    #--------------------------------------------------------------------------#
    #---------------------------- private -------------------------------------#
    #--------------------------------------------------------------------------#

    def __generate_cytoband_intervals(self):
        for cb in self.cytobands:
            self.cytoband_intervals.append({
                "no": int(cb["i"]),
                "id": f'{cb["chro"]}:{cb["start"]}-{cb["end"]}',
                "reference_name": cb["chro"],
                "cytobands": cb["cytoband"],
                "start": int(cb["start"]),
                "end": int(cb["end"]),
                "size": int(cb["end"]) - int(cb["start"])
            })


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def __generate_genomic_intervals(self):
        i_d = self.interval_definitions
        c_l = self.cytolimits

        # cytobands ################################################################
        if self.binning == "cytobands":
            self.genomic_intervals = deepcopy(self.cytoband_intervals)
            return

        # otherwise intervals ######################################################

        assert self.binning in i_d["genome_bin_sizes"]["values"].keys(), f'¡¡ Binning value "{self.binning}" not in list !!'

        int_b = i_d["genome_bin_sizes"]["values"][self.binning]
        e_p_f = i_d["terminal_intervals_soft_expansion_fraction"].get("value", 0.1)
        e_p = int_b * e_p_f

        i = 1
        for chro in c_l.keys():
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
                cbs = Cytobands().cytobands_label_from_positions(chro, start, end)

                self.genomic_intervals.append({
                    "no": i,
                    "id": f'{chro}{arm}:{start:09}-{end:09}',
                    "reference_name": chro,
                    "arm": arm,
                    "cytobands": f'{cbs}',
                    "start": start,
                    "end": end,
                    "size": size
                })

                start = end
                end += int_p
                i += 1

        self.interval_count = len(self.genomic_intervals)


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def __prepare_analysis_intervals(self):
        self.cov_labs = {"DUP": 'dup', "DEL": 'del'}
        self.hl_labs = {"HLDUP": "hldup", "HLDEL": "hldel"}
        self.maps = {
            "interval_count": self.interval_count,
            "binning": self.binning,
            "variant_count": 0
        }


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def __interval_cnv_coverage_arrays(self):
        self.coverage_maps = self.maps.copy()
        for cov_lab in self.cov_labs.values():
            self.coverage_maps.update({cov_lab: [0 for i in range(self.interval_count)]})
        for hl_lab in self.hl_labs.values():
            self.coverage_maps.update({hl_lab: [0 for i in range(self.interval_count)]})

        if type(self.analysis_variants).__name__ == "Cursor":
            self.analysis_variants.rewind()

        if (v_no := len(list(self.analysis_variants))) < 1:
            return

        self.coverage_maps.update({"variant_count": v_no})

        digests = set()
        self.duplicates = set()
        if type(self.analysis_variants).__name__ == "Cursor":
            self.analysis_variants.rewind()
        for v in self.analysis_variants:
            v_t_c = v.get("variant_state", {}).get("id", "__NA__")
            if v_t_c not in self.variant_type_definitions.keys():
                continue
            if not (dup_del := self.variant_type_definitions[v_t_c].get("DUPDEL")):
                # skipping non-CNV vars
                continue
            cov_lab = self.cov_labs[dup_del]
            hl_dupdel = self.variant_type_definitions[v_t_c].get("HLDUPDEL", "___none___")
            hl_lab = self.hl_labs.get(hl_dupdel)

            if not (v_i_id := v.get("variant_internal_id")):
                continue
            if v_i_id in digests:
                if "___shell___" in ENV:
                    BYC["WARNINGS"].append(v)
                    print(f'\n¡¡¡ {v_i_id} already counted for {v.get("analysis_id", None)}')
                    if v.get("_id"):
                        self.duplicates.add(v.get("_id"))
                continue
            else:
                digests.add(v_i_id)

            for i, intv in enumerate(self.genomic_intervals):
                if self.__has_overlap(intv, v):
                    ov_end = min(intv["end"], v["location"]["end"])
                    ov_start = max(intv["start"], v["location"]["start"])
                    ov = ov_end - ov_start
                    self.coverage_maps[cov_lab][i] += ov
                    if hl_lab:
                        self.coverage_maps[hl_lab][i] += ov


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def __interval_cnv_fraction_arrays(self):
        if not self.coverage_maps:
            self.__interval_cnv_coverage_arrays()
        self.fraction_maps = deepcopy(self.coverage_maps)

        if (self.coverage_maps.get("variant_count", 0)) < 1:
            return

        for cov_lab in self.cov_labs.values():
            for i, intv in enumerate(self.genomic_intervals):
                if (cov := self.fraction_maps[cov_lab][i]) > 0:
                    # correct fraction (since some intervals have a different size)
                    self.fraction_maps[cov_lab][i] = round(cov / intv["size"], 3)
        for hl_lab in self.hl_labs.values():
            for i, intv in enumerate(self.genomic_intervals):
                if (cov := self.fraction_maps[hl_lab][i]) > 0:
                    # correct fraction (since some intervals have a different size)
                    self.fraction_maps[hl_lab][i] = round(cov / intv["size"], 3)


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def __genome_cnv_statistics(self):
        if not self.coverage_maps:
            self.__interval_cnv_coverage_arrays()
        self.cnv_stats = {
            "cnvcoverage": 0,
            "dupcoverage": 0,
            "delcoverage": 0,
            "cnvfraction": 0,
            "dupfraction": 0,
            "delfraction": 0
        }
        self.chro_stats = {}

        for chro in self.cytolimits.keys():
            self.chro_stats.update({chro: deepcopy(self.cnv_stats)})
            for arm in ['p', 'q']:
                c_a = f'{chro}{arm}'
                self.chro_stats.update({c_a: deepcopy(self.cnv_stats)})

        if (self.coverage_maps.get("variant_count", 0)) < 1:
            return

        for cov_lab in self.cov_labs.values():
            for i, intv in enumerate(self.genomic_intervals):
                if (cov := self.coverage_maps[cov_lab][i]) > 0:
                    lab = f'{cov_lab}coverage'
                    chro = intv["reference_name"]
                    c_a = f'{chro}{intv["arm"]}'
                    self.cnv_stats[lab] += cov
                    self.chro_stats[chro][lab] += cov
                    self.chro_stats[c_a][lab] += cov
                    self.cnv_stats["cnvcoverage"] += cov
                    self.chro_stats[chro]["cnvcoverage"] += cov
                    self.chro_stats[c_a]["cnvcoverage"] += cov

        for s_k in self.cnv_stats.keys():
            if "coverage" in s_k:
                f_k = re.sub("coverage", "fraction", s_k)
                self.cnv_stats.update({s_k: int(self.cnv_stats[s_k])})
                self.cnv_stats.update({f_k: self.__round_frac(self.cnv_stats[s_k], self.genome_size, 3)})

                for chro in self.cytolimits.keys():
                    self.chro_stats[chro].update({s_k: int(self.chro_stats[chro][s_k])})
                    self.chro_stats[chro].update(
                        {f_k: self.__round_frac(self.chro_stats[chro][s_k], self.cytolimits[chro]['size'], 3)}
                    )
                    for arm in ['p', 'q']:
                        c_a = f'{chro}{arm}'
                        s_a = self.cytolimits[chro][arm][-1] - self.cytolimits[chro][arm][0]
                        self.chro_stats[c_a].update({s_k: int(self.chro_stats[c_a][s_k])})
                        self.chro_stats[c_a].update(
                            {f_k: self.__round_frac(self.chro_stats[c_a][s_k], s_a, 3)})


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def __has_overlap(self, interval, v):
        if not (chro := v["location"].get("chromosome")):
            prdbug(f'!!! no chromosome in variant !!!\n{v}')
            return False
        if interval["reference_name"] != chro:
            return False
        if v["location"]["start"] >= interval["end"]:
            return False
        if v["location"]["end"] <= interval["start"]:
            return False
        return True


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def __round_frac(self, val, maxval, digits=3):
        if (f := round(val / maxval, digits)) >1:
            f = 1
        return f


    ################################################################################

    def __interval_counts_from_analyses(self):
        """
        This method will analyze a set (either list or MongoDB Cursor) of Progenetix
        analyses with CNV statusmaps and return a list of standard genomic interval
        objects with added per-interval quantitative data.
        """
        min_f = self.interval_definitions["interval_min_fraction"].get("value", 0.001)
        self.interval_frequencies = deepcopy(self.genomic_intervals)
        int_no = self.interval_count

        pars = {
            "gain": {"cov_l": "dup", "hl_l": "hldup"},
            "loss": {"cov_l": "del", "hl_l": "hldel"}
        }

        self.analyses_count = 0
        # analyses can be either a list or a MongoDB Cursor (which has to be reset)
        if type(self.analyses).__name__ == "Cursor":
            self.analyses.rewind()

        f_factor = 0
        if (a_no := len(list(self.analyses))) > 0:
            f_factor = 100 / a_no
            self.analyses_count = a_no

        for t in pars.keys():
            covs = np.zeros((self.analyses_count, int_no))
            hls = np.zeros((self.analyses_count, int_no))
            # MongoDB specific
            if type(self.analyses).__name__ == "Cursor":
                self.analyses.rewind()
            cov_l = pars[t].get("cov_l")
            hl_l = pars[t].get("hl_l", cov_l)
            for i, analysis in enumerate(self.analyses):
                # the fallback is also a zeroed array ...
                covs[i] = analysis["cnv_statusmaps"].get(cov_l, [0] * int_no)
                hls[i] = analysis["cnv_statusmaps"].get(hl_l, [0] * int_no)

            # counting all occurrences of an interval for the current type > interval_min_fraction
            counts = np.count_nonzero(covs >= min_f, axis=0)
            frequencies = np.around(counts * f_factor, 3)
            hlcounts = np.count_nonzero(hls >= min_f, axis=0)
            hlfrequencies = np.around(hlcounts * f_factor, 3)

            for i, interval in enumerate(self.interval_frequencies):
                self.interval_frequencies[i].update({
                    f"{t}_frequency": frequencies[i],
                    f"{t}_hlfrequency": hlfrequencies[i]
                })

        if type(self.analyses).__name__ == "Cursor":
            self.analyses.close()
