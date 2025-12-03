import csv
from os import path
from pathlib import Path
from pymongo import MongoClient
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bycon import *
from byconServiceLibs import *

def _collect_analysis_ids(cs_coll):
    # which analysis to process
    ana_ids = BYC_PARS.get("analysis_ids", [])
    #limit = BYC_PARS.get("limit", 0)

    # if analysis_ids passed via CLI
    if ana_ids:
        return ana_ids

    # collect from Mongo
    ana_ids = []
    #for i, ana in enumerate(cs_coll.find({}, {"id": 1})):
    for ana in cs_coll.find({}, {"id" : 1}):
        ana_ids.append(ana["id"])
        #if limit and (i + 1) >= limit:
            #break

    return ana_ids

def _compute_gene_qc(dup, dele, gain_thr=0.3, del_thr=0.3):
    n_genes = len(dup)
    n_dup = 0
    n_del = 0
    n_any = 0
    for d, l in zip(dup, dele):
        is_dup = d >= gain_thr
        is_del = l >= del_thr
        if is_dup:
            n_dup += 1
        if is_del:
            n_del += 1
        if is_dup or is_del:
            n_any += 1
    return n_genes, n_dup, n_del, n_any

def main():
    assert_single_dataset_or_exit()
    ds_id = BYC["BYC_DATASET_IDS"][0]

    GB = GenomeBins()
    print(f'Using binning="{GB.get_genome_binning()}" with {GB.get_genome_bin_count()} intervals.')

    data_client = MongoClient(host=BYC_DBS["mongodb_host"])
    data_db = data_client[ds_id]
    cs_coll = data_db["analyses"]
    v_coll = data_db["variants"]

    ana_ids = _collect_analysis_ids(cs_coll)
    if not ana_ids:
        print("No analyses selected (analysisIds empty and no analyses found). Exiting.")
        return

    print(f"Will compute per-gene CNV maps for {len(ana_ids)} analyses from dataset '{ds_id}'.")

    intervals = GB.get_genome_bins()
    n_int = len(intervals)
    if n_int == 0:
        print("No genomic intervals found (check genome_binning / gene_interval_tsv). Exiting.")
        return

    out_path = BYC_PARS.get("outputfile") or "gene_cnv_test.tsv"
    out_path = path.abspath(out_path)
    qc_path = "gene_cnv_qc.tsv"
    qc_path = path.abspath(qc_path)
    print(f"Writing per-gene CNV fractions to: {out_path}")
    print(f"Writing per-analysis QC summary to: {qc_path}")

    with open(out_path, "w", newline="") as out_f, open(qc_path, "w", newline="") as qc_f:
        writer = csv.writer(out_f, delimiter="\t")
        qc_writer = csv.writer(qc_f, delimiter="\t")

        writer.writerow([
            "analysis_id",
            "gene_symbol",
            "gene_id",
            "chrom",
            "start",
            "end",
            "dup_frac",
            "del_frac",
            "hldup_frac",
            "hldel_frac",
        ])

        qc_writer.writerow([
            "analysis_id",
            "n_genes",
            "n_dup_genes",
            "n_del_genes",
            "n_any_genes",
            "cnvcoverage",
            "dupcoverage",
            "delcoverage",
            "cnvfraction",
            "dupfraction",
            "delfraction",
        ])

        gain_thr = float(BYC_PARS.get("gene_dup_threshold", 0.3))
        del_thr = float(BYC_PARS.get("gene_del_threshold", 0.3))

        #for ana_id in ana_ids:
        total_analyses = len(ana_ids)
        for idx, ana_id in enumerate(ana_ids, start=1):
            cs_vars = v_coll.find({"analysis_id": ana_id})
            maps, cnv_stats, chro_stats, duplicates = GB.getAnalysisFracMapsAndStats(
                analysis_variants=cs_vars
            )

            dup = maps.get("dup", [])
            dele = maps.get("del", [])
            hldup = maps.get("hldup", [])
            hldel = maps.get("hldel", [])

            if not (len(dup) == len(dele) == len(hldup) == len(hldel) == n_int):
                print(f"WARNING: interval length mismatch for analysis {ana_id}; skipping.")
                continue

            for i, intv in enumerate(intervals):
                writer.writerow([
                    ana_id,
                    intv.get("gene_symbol", ""),
                    intv.get("id", ""),
                    intv.get("reference_name", ""),
                    intv.get("start", ""),
                    intv.get("end", ""),
                    dup[i],
                    dele[i],
                    hldup[i],
                    hldel[i],
                ])

            n_genes, n_dup, n_del, n_any = _compute_gene_qc(dup, dele, gain_thr=gain_thr, del_thr=del_thr)

            qc_writer.writerow([
                ana_id,
                n_genes,
                n_dup,
                n_del,
                n_any,
                cnv_stats.get("cnvcoverage", 0),
                cnv_stats.get("dupcoverage", 0),
                cnv_stats.get("delcoverage", 0),
                cnv_stats.get("cnvfraction", 0.0),
                cnv_stats.get("dupfraction", 0.0),
                cnv_stats.get("delfraction", 0.0),
            ])

            if idx % 1000 == 0 or idx == total_analyses:
                print(f"[testgenemap] Processed {idx}/{total_analyses} analyses")

    print("Done.")


if __name__ == "__main__":
    main()