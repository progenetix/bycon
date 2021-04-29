#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os
from os import path
from pymongo import MongoClient

"""
## ` Cancer Topography Annontation Converter: SEER to NCIt `
##  Note: this is an approximation, as only the first mentioned ICD-O-3 site is considered for conversion.

"""

# Set up working directory:
dir_path = path.dirname( path.abspath(__file__) )
os.chdir(dir_path)

# Prepare dataframes:
df_old = pd.read_csv('old_icdo_index.txt', sep='\t') # converts old codes into the related ICD-O-3

df_convert = pd.read_csv('ICD-O-3.1-NCIt_Topography_Mapping.txt', sep="\t") # converts ICD-O-3 Topograpy into NCIt Site codes
df_convert = df_convert.rename(columns = {'ICD-O Code': 'ICDO_Code'})     

##############################################################################
##############################################################################
##############################################################################

def main():
    update_ncit_tumor_type()
    
##############################################################################

def converter(pubs):
        
    pubs_info = []
    for pub in pubs: 
        pubs_info.append([pub['id'], pub['cancertype'], pub['counts']['genomes']])
    
    # Make list of the old codes found in the publication collection:
    old_codes = []
    for pub in pubs_info:
        code = pub[1].replace(':', ' ')
        code = code.split(' ')
        if len(code) > 1: 
            old_codes.append([pub[0], int(code[1]), pub[2]])  # extract PMID, old_code and n_samples
    
    # For each old SEER code get 1st mentioned ICD-O-3 Site code: 
    icdo3 = []
    for info in old_codes:
        for code in df_old['Recode']:
            if info[1] == code:
                icdos = []
                icdo_site = df_old[df_old.Recode == code].iloc[0][0] # select a row and select 'ICD-O-3 Site' column
                clean_icdo = icdo_site.replace('-', ' ')
                clean_icdo = clean_icdo.replace(', ', ' ')
                clean_icdo = clean_icdo.replace(',', ' ')
                first_icdo = clean_icdo.split(' ')[0] # generate list of ICD-O-3 Sites and select the 1st one with [0]

                if code == 99999:
                    print(f'Warning: site or histology code for {info[0]} not within valid range or site code not found in this table.')
                else:
                    icdos.append([first_icdo, info[0], info[1], info[2]]) # extract new codes, PMID, old codes and n_samples
        
        icdo3.extend(icdos)
            
    # Convert ICD-O-3 codes in NCIt codes:
    converted = []
    for pub in icdo3:
        for code in df_convert['ICDO_Code']:
            clean_code = code.replace('.', '')
            if clean_code == pub[0]:
                c = []
                info = df_convert[df_convert.ICDO_Code == code].iloc[0]
                ncit = info[6] # NCIt Topography code
                ncit_term = info[7] # NCIt Preferred Term
                c.append([code, ncit, ncit_term, pub[1], pub[2], pub[3]]) # extract icdo, ncit, ncit_term, PMID, old codes and n_samples
        converted.append(c)   
        
    return converted

##############################################################################

def isNaN(value):
    try:
        import math
        return math.isnan(float(value))
    except:
        return False    

##############################################################################

def make_ncit_annotation(converted):

    sample_types = []
    for old_code in converted: 
        tumor_types = {}
        
        info = old_code[0] 
        icdo = info[0]
        ncit = info[1]
        ncit_term = info[2]
        pmid = info[3]
        old_seer = info[4]
        counts = info[5]
        
        if isNaN(ncit) == False: 
            tumor_types.update({"pmid": pmid})
            tumor_types.update({"sample_types": {"id": ncit,
                                "label": str(ncit_term) + " (ICD-O-3 to NCIt Topography Mapping)",
                                "counts": counts}
                                })
            tumor_copy = tumor_types.copy()
            sample_types.append(tumor_copy)
        
        else:
            if old_seer == '37000':
                tumor_types.update({"pmid": pmid})
                tumor_types.update({"sample_types": {"id": "NCIT:C3262",
                                    "label": "Neoplasm",
                                    "counts": counts}
                                    })
                tumor_copy = tumor_types.copy()
                sample_types.append(tumor_copy)
                    
            else:
                tumor_types.update({"pmid": pmid})
                tumor_types.update({"sample_types": {"id": f'No Topography NCIt code available for the ICD-O-3 site code {icdo}',
                                    "counts": counts}
                                    })
                tumor_copy = tumor_types.copy()
                sample_types.append(tumor_copy)
        

    return sample_types 

##############################################################################

def update_ncit_tumor_type():
    
    # Connect to database:
    client = MongoClient() 
    cl = client['progenetix'].publications
    to_convert = cl.find({'cancertype': {'$exists': True}}) # 917 publications w/ 'cancertype' annotation
    converted = converter(to_convert)
    new_annotations = make_ncit_annotation(converted)    
    
    # Update the database
    for post in new_annotations:  
        print(post['sample_types'])
        cl.update_one({'id': post['pmid']}, {'$rename': {'cancertype': 'sample_types'}})
        cl.find({'cancertype': {'$exists': True}}).count() # check that we don't have as many 'cancertyp'e annotations anymore
        cl.update_one({'id': post['pmid']}, {'$set': {'sample_types': post['sample_types']}})
        print(f'Tumor type annotation was updated for the publication with "id" {post["pmid"]}.')   

##############################################################################

if __name__ == '__main__':
    main()

##############################################################################
##############################################################################
##############################################################################

