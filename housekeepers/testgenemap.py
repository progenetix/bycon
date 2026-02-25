#!/usr/local/bin/python3

import csv
from os import path
from os import environ
from progress.bar import Bar

from pathlib import Path
from pymongo import MongoClient
import sys

from bycon import *
from byconServiceLibs import *

# ./housekeepers/testgenemap.py -d progenetix --genomeBinning genes --geneIntervalTsv "cancer_gene_list.tsv" --limit 0

################################################################################

def main():
    assert_single_dataset_or_exit()
    ds_id = BYC["BYC_DATASET_IDS"][0]
    BYC_PARS["filters"] = [{"id": "EFO:0009656"}]  # "neoplastic sample"
    output_path = path.join("/", "Users", environ.get('USER'), "Downloads", "gene_cnv_test.tsv")
    output_file = BYC_PARS.get("outputfile") or output_path

    GB = GenomeBins()
    print(f'Using binning="{GB.getGenomeBinningID()}" with {GB.getGenomeBinCount()} intervals.')

    data_client = MongoClient(host=BYC_DBS["mongodb_host"])
    data_db = data_client[ds_id]
    v_coll = data_db["variants"]

    ana_ids = BYC_PARS.get("analysis_ids", [])
    if len(ana_ids) < 1:
        record_queries = ByconQuery().recordsQuery() # will be populated from the filter...
        DR = ByconDatasetResults(ds_id, record_queries)
        ds_results = DR.retrieveResults()
        ana_ids = ds_results["analyses.id"]["target_values"]
        print(f"Collected {len(ana_ids)} analysis IDs from dataset results based on filters.")

    if len(ana_ids) < 1:
        print("No analyses selected (analysisIds empty and no analyses found). Exiting.")
        return

    print(f"Will compute per-gene CNV maps for {len(ana_ids)} analyses from dataset '{ds_id}'.")

    intervals = GB.getGenomeBins()
    n_int = len(intervals)
    if n_int == 0:
        print("No genomic intervals found (check genome_binning / gene_interval_tsv). Exiting.")
        return

    print(f"Writing per-gene CNV fractions to: {output_file}")

    with open(output_file, "w", newline="") as out_f:
        writer = csv.writer(out_f, delimiter="\t")
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

        #for ana_id in ana_ids:

        total_analyses = len(ana_ids)
        bar = Bar("{} analyses".format(ds_id), max = total_analyses, suffix='%(percent)d%%'+" of "+str(total_analyses) )
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

            if idx % 1000 == 0 or idx == total_analyses:
                print(f"\n[testgenemap] Processed {idx}/{total_analyses} analyses")
            bar.next()
        bar.finish()
    print("Done.")



################################################################################
################################################################################
################################################################################

if __name__ == "__main__":
    main()