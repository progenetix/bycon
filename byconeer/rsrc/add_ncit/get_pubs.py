#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pymongo import MongoClient

'''

Script to find publications in the database without a cancer type annotation.

'''

# Connect to mongo and load publication collection
client = MongoClient()
cl = client['progenetix'].publications

# Find publications with no cancer type annotations for a specific year (e.g., 2017)
objs = cl.find( {'$and': [ {'sample_types': {'$exists': False}},
                           {'year': '2017'},
                           {'counts.genomes': {'$gt': 0}} # $gt: 0 = greater than 0
                           ]} )

# Extract publication's pmid and total number of samples (1st column of annotation table)
n=0
for obj in objs:
    pmid = obj['id']
    n_samples = obj['counts']['genomes']
    print(pmid[5:], n_samples)