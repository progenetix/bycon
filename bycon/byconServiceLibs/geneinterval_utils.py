import csv
from os import path
from bycon import BYC, BYC_PARS

class GeneIntervals:
    def __init__(self, tsv_path=None):
        if tsv_path is None:
            tsv_path = BYC_PARS.get("gene_interval_tsv")
        if not tsv_path:
            raise ValueError("No TSV path provided for gene intervals (gene_interval_tsc is empty).")
        
        self.tsv_path = path.normpath(tsv_path)
        self._genes = self._load_genes()
    
    def _load_genes(self):
        required = {"gene_id", "gene_symbol", "chrom", "start", "end"}
        genes = []
        with open(self.tsv_path, "r") as f:
            reader = csv.DictReader(f, delimiter="\t")
            header = set(reader.fieldnames or [])
            missing = required - header
            if missing:
                raise ValueError(f"GeneInterval TSV {self.tsv_path} is missing required columns:{sorted(missing)}")
            for row in reader:
                try: 
                    start = int(row["start"])
                    end = int(row["end"])
                except (TypeError, ValueError):
                    continue
                gene = dict(row)
                gene["start"] = start
                gene["end"] = end
                genes.append(gene)
        return genes
    
    def _as_intervals(self):
        intervals = []
        for g in self._genes:
            # keep the basic
            gene_id = g.get("gene_id")
            gene_symbol = g.get("gene_symbol")
            chrom = g.get("chrom")
            start = g.get("start")
            end = g.get("end")
            # others go to info
            base_keys = {"gene_id", "gene_symbol", "chrom", "start", "end"}
            info = {k : v for k,v in g.items() if k not in base_keys}
            intervals.append({
                "id": gene_id,
                "symbol": gene_symbol,
                "chromosome": chrom,
                "start": start,
                "end": end,
                "info": info
            })
        return intervals

