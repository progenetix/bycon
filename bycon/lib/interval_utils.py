import re
import sys

import numpy as np

from copy import deepcopy
from os import pardir, path

# ------------------------------- bycon imports -------------------------------#

from bycon_helpers import ByconMongo, prdbug
from config import BYC, BYC_DBS, BYC_PARS, HTTP_HOST
from genome_utils import Cytobands, GeneIntervals

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
in `genome_definitions.genome_bin_sizes` (e.g. 1Mb => 1000000).

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
    def __init__(self, binning=None):
        self.genome_definitions = BYC.get("genome_definitions", {})
        self.variant_type_definitions = BYC.get("variant_type_definitions", {})

        if binning:       
            self.binning = binning
        else:
            self.binning = BYC_PARS.get("genome_binning", "1Mb")

        self.cnv_lengths    = False

        self.CB             = Cytobands()
        self.cytolimits     = self.CB.get_all_cytolimits()
        self.genome_size    = self.CB.get_genome_size()

        self.int_min_frac   =   self.genome_definitions.get("interval_min_fraction", {}).get("value", 0.001)
 
        self.genomic_intervals  = []
        self.cytoband_intervals = []

        self.genome_definitions.update({"genome_binning": self.binning})

        self.__generate_cytoband_intervals()
        self.__generate_genomic_intervals()

    # -------------------------------------------------------------------------#
    # ----------------------------- public -------------------------------------#
    # -------------------------------------------------------------------------#

    def getGenomeBinningID(self):
        return self.binning

    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def getGenomeBins(self):
        return self.genomic_intervals

    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def getGenomeBinCount(self):
        return len(self.genomic_intervals)


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def getAnalysisFracMapsAndStats(self, analysis_variants=[]):
        self.analysis_variants = analysis_variants
        self.__process_analysis_intervals_for_cnvs()
        return (
            self.fraction_maps,
            self.cnv_stats,
            self.chro_stats,
            list(self.duplicates),
        )


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def getAnalysisCNVintervals(self, analysis_variants=[]):
        self.analysis_variants = analysis_variants
        self.cnv_lengths = True
        self.__process_analysis_intervals_for_cnvs()
        self.coverage_intervals = []        
        self.__interval_cnv_coverage_objects()
        return self.coverage_intervals

    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def intervalFrequencyMaps(self, analyses=[]):
        self.analyses = analyses
        self.__interval_counts_from_analyses()
        return self.interval_frequencies, self.analyses_count


    # -------------------------------------------------------------------------#
    # ---------------------------- private ------------------------------------#
    # -------------------------------------------------------------------------#

    def __generate_cytoband_intervals(self):
        for cb in self.CB.get_all_cytobands():
            self.cytoband_intervals.append({
                "no": int(cb["no"]),
                "id": f'{cb["chro"]}:{cb["start"]}-{cb["end"]}',
                "reference_name": cb["chro"],
                "cytobands": cb["cytoband"],
                "start": int(cb["start"]),
                "end": int(cb["end"]),
                "size": int(cb["end"]) - int(cb["start"])
            })


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#
    
    def __generate_gene_intervals(self):
        # generate genomic intervals from a gene list
        # the list will be sorted by genomic start position
        genes   = GeneIntervals().get_all_genes()
        c_l     = self.cytolimits

        self.genomic_intervals = []
        no = 1
        for chro in c_l.keys():
            chro_genes = [ g for g in genes if g.get("chrom") == chro ]
            chro_genes = sorted(chro_genes, key=lambda g: g.get("start", 0))

            for g in chro_genes:
                chro            = g.get("chrom")
                start           = g.get("start")
                end             = g.get("end")
                gene_id         = g.get("gene_id", "")
                gene_symbol     = g.get("gene_symbol", gene_id or "")
                gene_type       = g.get("gene_type", "")

                cbs = str(self.CB.cytobands_label_from_positions(chro, start, end))
                # base_keys = {"gene_id", "gene_symbol", "gene_type", "chrom", "start", "end", "no"}
                # info = {k: v for k, v in g.items() if k not in base_keys}

                self.genomic_intervals.append({
                    "no": no,
                    "id": gene_id or gene_symbol,
                    "reference_name": chro,
                    "cytobands": cbs,
                    "start": start,
                    "end": end,
                    "size": end - start,
                    "gene_symbol": gene_symbol,
                    # "info": info
                })
                no += 1

        self.interval_count = len(self.genomic_intervals)


    #--------------------------------------------------------------------------#
    #--------------------------------------------------------------------------#

    def __generate_genomic_intervals(self):
        i_d = self.genome_definitions
        c_l = self.cytolimits

        # cytobands ############################################################
        if self.binning == "cytobands":
            self.genomic_intervals = deepcopy(self.cytoband_intervals)
            return

        # gene intervals #######################################################
        if self.binning.startswith("genes"):
            self.__generate_gene_intervals()
            return
        
        # otherwise intervals ##################################################
        assert self.binning in i_d["genome_bin_sizes"]["values"].keys(), f'¡¡ Binning value "{self.binning}" not in list !!'

        int_b = i_d["genome_bin_sizes"]["values"][self.binning]
        e_p_f = i_d["terminal_intervals_soft_expansion_fraction"].get("value", 0.1)
        e_p = int_b * e_p_f

        no = 1
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

                self.genomic_intervals.append(
                    {
                        "no": no,
                        "id": f"{chro}{arm}:{start:09}-{end:09}",
                        "reference_name": chro,
                        "cytobands": f"{cbs}",
                        "start": start,
                        "end": end,
                        "size": size,
                    }
                )

                start = end
                end += int_p
                no += 1

        self.interval_count = len(self.genomic_intervals)


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __process_analysis_intervals_for_cnvs(self):
        self.__prepare_analysis_intervals()
        self.__interval_cnv_coverage_arrays()
        self.__interval_cnv_fraction_arrays()
        self.__genome_cnv_statistics()


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __prepare_analysis_intervals(self):
        self.cov_labs = {"DUP": "dup", "DEL": "del"}
        self.hl_labs = {"HLDUP": "hldup", "HLDEL": "hldel"}
        self.maps = {
            "interval_count": self.interval_count,
            "binning": self.binning,
            "variant_count": 0,
        }


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __interval_cnv_coverage_arrays(self):
        # Initialize coverage maps with default values
        self.coverage_maps  = {}
        self.segments_stash = False
        if self.cnv_lengths:
            self.segments_stash = {}
        self.coverage_maps.update({"variant_count": 0})
        for label in {**self.cov_labs, **self.hl_labs}.values():
            self.coverage_maps.update({label: []})
            for i in range(0, self.interval_count):
                self.coverage_maps[label].append(0)
            if self.cnv_lengths:
                self.segments_stash.update({label: []})
                for i in range(0, self.interval_count):
                    self.segments_stash[label].append(set())

        # Handle empty or non-iterable analysis_variants
        if type(self.analysis_variants).__name__ == "Cursor":
            self.analysis_variants.rewind()

        digests         = set()
        self.duplicates = set()

        for variant in self.analysis_variants:
            # skipping non-CNV vars
            if "CopyNumberChange" not in variant.get("type", ""):
                continue

            variant_state_id = variant.get("variant_state", {}).get("id")
            if variant_state_id not in self.variant_type_definitions:
                continue

            variant_def = self.variant_type_definitions[variant_state_id]
            cov_label   = self.cov_labs.get(variant_def.get("DUPDEL"))
            hl_label    = self.hl_labs.get(variant_def.get("HLDUPDEL"))

            if not cov_label:
                continue

            if not (v_i_id := variant.get("variant_internal_id")):
                continue
            if v_i_id in digests:
                if "___shell___" in HTTP_HOST:
                    BYC["WARNINGS"].append(variant)
                    print(
                        f"\n¡¡¡ {v_i_id} already counted for {variant.get('analysis_id')}"
                    )
                    if variant.get("_id"):
                        self.duplicates.add(variant.get("_id"))
                continue

            digests.add(v_i_id)

            for i, intv in enumerate(self.genomic_intervals):
                if self.__has_overlap(intv, variant):
                    i_s = intv["start"]
                    i_e = intv["end"]
                    v_s = variant["location"]["start"]
                    v_e = variant["location"]["end"]
                    v_l = v_e - v_s
                    overlap_end     = min(i_e, v_e)
                    overlap_start   = max(i_s, v_s)
                    overlap_length  = overlap_end - overlap_start
                    self.coverage_maps[cov_label][i] += overlap_length
                    # print(f"cov {cov_label} - {i}: {intv["reference_name"]}:{i_s}-{i_e} => {variant["location"].get("chromosome")}:{v_s}-{v_e}")
                    if self.segments_stash:
                        self.segments_stash[cov_label][i].add(v_l)
                        # print(f"cov {cov_label} - {i}: {self.segments_stash[cov_label][i]} => {self.coverage_maps[cov_label][i]}")
                    if hl_label:
                        self.coverage_maps[hl_label][i] += overlap_length
                        if self.segments_stash:
                            self.segments_stash[hl_label][i].add(v_l)

            self.coverage_maps["variant_count"] += 1


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __interval_cnv_coverage_objects(self):
        if (self.coverage_maps.get("variant_count", 0)) < 1:
            return

        for i, intv in enumerate(self.genomic_intervals):
            i_stats = {}
            for cov_lab in {**self.cov_labs, **self.hl_labs}.values():
                # i_stats[cov_lab] = self.coverage_maps[cov_lab][i]
                i_stats[cov_lab] = self.fraction_maps[cov_lab][i]
                # i_stats[f"{cov_lab}_fraction"] = self.fraction_maps[cov_lab][i]

            if any(value > 0 for value in i_stats.values()):
                pos_int = deepcopy(intv)
                pos_int.update(i_stats)
                max_seg = 0
                for cov_lab in {**self.cov_labs, **self.hl_labs}.values():
                    if (segs := self.segments_stash[cov_lab][i]):
                        if (max_s := max(segs)) > max_seg:
                            max_seg = max_s
                        pos_int.update({f"{cov_lab}_max_segment": max_s})
                pos_int.update({"max_segment": max_seg})
                for pk in ["reference_name", "cytobands", "start", "end", "info"]:
                    pos_int.pop(pk, None)
                self.coverage_intervals.append(pos_int)


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

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


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __genome_cnv_statistics(self):
        if not self.coverage_maps:
            self.__interval_cnv_coverage_arrays()
        self.cnv_stats = {
            "cnvcoverage": 0,
            "dupcoverage": 0,
            "delcoverage": 0,
            "cnvfraction": 0,
            "dupfraction": 0,
            "delfraction": 0,
        }

        self.chro_stats = {}
        for chro in self.cytolimits.keys():
            self.chro_stats.update({chro: deepcopy(self.cnv_stats)})
            for arm in ["p", "q"]:
                c_a = f"{chro}{arm}"
                self.chro_stats.update({c_a: deepcopy(self.cnv_stats)})

        if (self.coverage_maps.get("variant_count", 0)) < 1:
            return

        for cov_lab in self.cov_labs.values():
            for i, intv in enumerate(self.genomic_intervals):
                if (cov := self.coverage_maps[cov_lab][i]) > 0:
                    lab = f"{cov_lab}coverage"
                    chro = intv["reference_name"]
                    arm = "q"
                    if "p" in (cb := intv.get("cytobands", "___none___")):
                        arm = "p"
                    c_a = f"{chro}{arm}"
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
                self.cnv_stats.update(
                    {f_k: self.__round_frac(self.cnv_stats[s_k], self.genome_size, 3)}
                )

                for chro in self.cytolimits.keys():
                    self.chro_stats[chro].update({s_k: int(self.chro_stats[chro][s_k])})
                    self.chro_stats[chro].update(
                        {
                            f_k: self.__round_frac(
                                self.chro_stats[chro][s_k],
                                self.cytolimits[chro]["size"],
                                3,
                            )
                        }
                    )
                    for arm in ["p", "q"]:
                        c_a = f"{chro}{arm}"
                        s_a = (
                            self.cytolimits[chro][arm][-1]
                            - self.cytolimits[chro][arm][0]
                        )
                        self.chro_stats[c_a].update(
                            {s_k: int(self.chro_stats[c_a][s_k])}
                        )
                        self.chro_stats[c_a].update(
                            {f_k: self.__round_frac(self.chro_stats[c_a][s_k], s_a, 3)}
                        )

    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __has_overlap(self, interval, v):
        if not (chro := v["location"].get("chromosome")):
            prdbug(f"!!! no chromosome in variant !!!\n{v}")
            return False
        if interval["reference_name"] != chro:
            return False
        if v["location"]["start"] >= interval["end"]:
            return False
        if v["location"]["end"] <= interval["start"]:
            return False
        return True


    # -------------------------------------------------------------------------#

    def __round_frac(self, val, maxval, digits=4):
        if (f := round(val / maxval, digits)) > 1:
            f = 1
        return f


    # -------------------------------------------------------------------------#

    def __interval_counts_from_analyses(self):
        """
        This method will analyze a set (either list or MongoDB Cursor) of Progenetix
        analyses with CNV statusmaps and return a list of standard genomic interval
        objects with added per-interval quantitative data.
        """

        pars = {
            "gain": {"cov_l": "dup", "hl_l": "hldup"},
            "loss": {"cov_l": "del", "hl_l": "hldel"},
        }

        # analyses can be either a list or a MongoDB Cursor (which has to be
        # reset after accessing its contents)
        if type(self.analyses).__name__ == "Cursor":
            self.analyses.rewind()

        self.analyses_count = 0
        self.interval_frequencies = deepcopy(self.genomic_intervals)

        f_factor = 0
        if (a_no := len(list(self.analyses))) > 0:
            f_factor = 100 / a_no
            self.analyses_count = a_no

        # iterating for gain and loss types (keys in `pars`)
        for t in pars.keys():
            covs    = np.zeros((self.analyses_count, self.interval_count))
            hls     = np.zeros((self.analyses_count, self.interval_count))

            # MongoDB specific
            if type(self.analyses).__name__ == "Cursor":
                self.analyses.rewind()

            cov_l   = pars[t].get("cov_l")
            hl_l    = pars[t].get("hl_l", cov_l)
            for i, analysis in enumerate(self.analyses):
                # the fallback is also a zeroed array ...
                covs[i] = analysis["cnv_statusmaps"].get(cov_l, [0] * self.interval_count)
                hls[i]  = analysis["cnv_statusmaps"].get(hl_l,  [0] * self.interval_count)

            # counting all occurrences of an interval for the current type > interval_min_fraction
            counts          = np.count_nonzero(covs >= self.int_min_frac, axis=0)
            frequencies     = np.around(counts * f_factor, 3)
            hlcounts        = np.count_nonzero(hls >= self.int_min_frac, axis=0)
            hlfrequencies   = np.around(hlcounts * f_factor, 3)

            for i, interval in enumerate(self.interval_frequencies):
                self.interval_frequencies[i].update({
                    f"{t}_frequency": frequencies[i],
                    f"{t}_hlfrequency": hlfrequencies[i],
                })

        if type(self.analyses).__name__ == "Cursor":
            self.analyses.close()
