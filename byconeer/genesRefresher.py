#!/usr/local/bin/python3

import re, json, yaml
from os import path, environ, pardir
import sys, datetime
import argparse
from pymongo import MongoClient
from progress.bar import Bar
from pathlib import Path

from typing import List

from ncbi.datasets.openapi import ApiClient as DatasetsApiClient
from ncbi.datasets.openapi import ApiException as DatasetsApiException
from ncbi.datasets.openapi import GeneApi as DatasetsGeneApi
# from ncbi.datasets.openapi.models import V1GeneMatch

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

################################################################################
################################################################################
################################################################################

"""
./ontologyTermLister.py -c rsrc/NCITstage/NCITstage-codes.tsv -l rsrc/NCITstage/NCITstage-labels.tsv -o rsrc/NCITstage/numbered-hierarchies.tsv
"""

################################################################################
################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--genesymbols", help="gene symbols, comma-separated")
    parser.add_argument("-f", "--forcerefresh", help="overwrite old data for the gene")
    parser.add_argument("-t", "--test", help="test setting")
   
    return parser.parse_args()

################################################################################

def main():

    args = _get_args()

    if args.test:
        print( "¡¡¡ TEST MODE - no db update !!!")

    data_client = MongoClient( )
    data_db = data_client[ "progenetix" ]
    gene_coll = data_db[ "genes" ]

    # TODO: move to config file
    hgnc_f = Path( path.join( dir_path, "rsrc", "HGNC", "HGNC-genes.json" ) )
    grch38_f = Path( path.join( dir_path, "rsrc", "GRCh38", "GRCh38-chromosomes.tsv" ) )
    taxon = 'human'
    p_list = "gene_id ensembl_gene_ids nomenclature_authority omim_ids orientation swiss_prot_accessions symbol synonyms type annotations genomic_ranges".split()

    gene_symbols = []
    if args.genesymbols:
        gene_symbols = re.split(",", args.genesymbols)
    else:
        with open(hgnc_f, 'r') as g_f:
            g_d = g_f.read()
            hgnc = json.loads(g_d)
            for g in hgnc:
                gene_symbols.append(g["symbol"])

    existing_symbols = gene_coll.distinct( "symbol" )

    g_no_all = len(gene_symbols)
    g_no = 0

    if not args.test:
        bar = Bar("Updating ", max = g_no_all, suffix='%(percent)d%%'+" of "+str(g_no_all) )

    with DatasetsApiClient() as api_client:
        gene_api = DatasetsGeneApi(api_client)
        for gs in gene_symbols:
            if not args.test:
                bar.next()
            if gs in existing_symbols:
                if not args.forcerefresh:
                    print("\nskipping {} - exists and no forced refresh `-f 1`".format(gs))
                    continue
            try:
                # For a single species retrieve gene metadata using a list of gene symbols
                try:
                    gene_reply = gene_api.gene_metadata_by_tax_and_symbol([gs], taxon)
                    for gene in gene_reply.genes:
                        g_input = gene.gene.to_dict()

                        g_update = {}
                        for p in p_list:
                            if p in g_input:
                                g_update.update({p:g_input[p]})
                        g_update.update({"reference_name":g_input["chromosomes"][0]})
                        g_update.update({"gene_type":g_input["type"]})

                        if g_input["genomic_ranges"]:
                            g_update.update({"accession_version":g_input["genomic_ranges"][0]["accession_version"]})
                            g_update.update({"start": int(g_input["genomic_ranges"][0]["range"][0]["begin"]), "end": int(g_input["genomic_ranges"][0]["range"][0]["end"]) })
                            g_update.update({"gene_locus_length": g_update["end"] - g_update["start"]})
  
                        if not args.test:
                            gene_coll.update_one({"symbol":g_update["symbol"]}, {"$set": g_update }, upsert=True )
                        else:
                            print(json.dumps(g_update, indent=4, sort_keys=True, default=str)+"\n")

                        g_no += 1
                except:
                    continue

            except DatasetsApiException as e:
                print(f'Exception when calling GeneApi: {e}\n')

    if not args.test:
        bar.finish()

    print("===> Found {} of {} genes".format(g_no, g_no_all))

################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    main()
