#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pymongo import MongoClient
import pandas as pd
import os
from os import path
from publication_utils import get_ncit_tumor_type

dir_path = path.dirname( path.abspath(__file__) )
os.chdir(dir_path)

'''

This script can be used to generate sample types annotations in posts of the 
Progenetix publication collection that don't have any.
These posts can be found with the get_pubs.py script.

Annotation about the tumor types is done manually on a .tsv table.

Format of the table:

PMID counts [\t] NCIT code, counts [\t] tumor name 
    
'''

# Connect to database:
client = MongoClient()
cl = client['progenetix'].publications

# Read table with sample type annotations:
df = pd.read_csv("sample_types.txt", sep="\t")

# Generate sample type annotations:
print('... Generating sample type annotations ...')
for i, info in df.iterrows():
    pmid = info['PMID, n_samples'].split(' ')[0]
    tumors = info['Sample Types']
    fullNames = info['Tumor Names']
    sample_types = get_ncit_tumor_type(tumors, fullNames)
    
    # Generate 'sample_types' field and fill it in with annotations from table: 
    result = cl.update_one({'id': 'PMID:'+pmid}, {'$set': {'sample_types': sample_types}})
    if result.matched_count > 0:
        print(f'Update was successfull for the publication with "id" PMID:{pmid}.')

# Check that process works:
test = cl.find({'id': 'PMID:29203589'})
for pub in test:
    print(pub)

    
    

