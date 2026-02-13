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
    ana_ids = BYC_PARS.get("analysis_ids", [])

    if ana_ids:
        return ana_ids

    collected = []
    pipeline = [
        {
            "$lookup": {
                "from": "biosamples",
                "localField": "biosample_id",
                "foreignField": "id",
                "as": "bs",
            }
        },
        {"$unwind": "$bs"},
        {
            "$match": {
                "bs.biosample_status.label": {"$ne": "reference sample"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "id": 1,
            }
        },
    ]

    for doc in cs_coll.aggregate(pipeline):
        ana_id = doc.get("id")
        if ana_id:
            collected.append(ana_id)
    
    return collected

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

    # TODO: No hardcoded paths
    downloads_dir = "/Users/bgadmin/Downloads"
    out_name = BYC_PARS.get("outputfile") or "gene_cnv_test.tsv"
    out_name = path.basename(out_name)  
    out_path = path.join(downloads_dir, out_name)
    print(f"Writing per-gene CNV fractions to: {out_path}")

    with open(out_path, "w", newline="") as out_f:
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
                print(f"[testgenemap] Processed {idx}/{total_analyses} analyses")

    print("Done.")


if __name__ == "__main__":
    main()