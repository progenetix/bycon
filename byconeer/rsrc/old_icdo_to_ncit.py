#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 22 09:04:41 2021

@author: sofiapfund
"""

import pandas as pd
import os
from os import path
from pymongo import MongoClient

"""

`Cancer Topography Annontation Converter`

Note: this is an unprecise method, as only the first mentioned ICD-O-3 site is considered for conversion from old to new ICD-O;
and only the first mentioned new ICD-O-3 is used for conversion to NCIt.

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
    icdo3 = {}
    for info in old_codes:
        for code in df_old['Recode']:
            if info[1] == code:
                if info[0] not in icdo3:
                    icdo_site = df_old[df_old.Recode == code].iloc[0][0] # select a row and select 'ICD-O-3 Site' column
                    clean_icdo = icdo_site.replace('-', ' ')
                    clean_icdo = clean_icdo.replace(', ', ' ')
                    clean_icdo = clean_icdo.replace(',', ' ')
                    first_icdo = clean_icdo.split(' ')[0] # generate list of ICD-O-3 Sites and select the 1st one with [0]
    
                    if code == 99999:
                        print(f'Warning: site or histology code for {info[0]} not within valid range or site code not found in this table.')
                    else:
                    
                        icdo3[info[0]] = []
                        icdo3[info[0]] = [first_icdo, info[1], info[2]] # extract new codes, old codes and n_samples
    
    
    # Dictionary of ICD-O-3 codes and the corresponding NCIt terms:
    codes = {}
    for code in df_convert['ICDO_Code']:
            clean_code = code.replace('.', '')
            info = df_convert[df_convert.ICDO_Code == code].iloc[0]
            ncit = info[6] # NCIt Topography code
            ncit_term = info[7] # NCIt Preferred Term
            if clean_code not in codes:
                codes[clean_code] = []
                codes[clean_code] = [code, ncit, ncit_term]
   
    # Convert ICD-O-3 codes in NCIt codes:
    converted = {} 
    for pub in icdo3:
        converted[pub] = []
        icdo = icdo3[pub][0]
        if icdo in codes:
            converted[pub] = [codes[icdo][0], codes[icdo][1], codes[icdo][2], icdo3[pub][1], icdo3[pub][2]] # extract icdo, ncit, ncit_term, old codes and n_samples
        else:
            print(f"Warning: unknown primary site in {pub} (no corresponding NCIt code was found for the ICDO-3 site {icdo}).")
            converted[pub] = [icdo, icdo3[pub][1], icdo3[pub][2]] # extract icdo, old codes and n_samples
    
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
        
    for publication in converted: 

        tumor_types = {}
        
        if len(converted[publication]) == 5:
            info = converted[publication]
            icdo = info[0]
            ncit = info[1]
            ncit_term = info[2]
            old_seer = info[3]
            counts = info[4]
            
            if isNaN(ncit) == False: 
                tumor_types.update({"pmid": publication})
                tumor_types.update({"sample_types": {"id": ncit,
                                    "label": str(ncit_term) + " (ICD-O-3 to NCIt Topography Mapping)",
                                    "counts": counts}
                                    })
                tumor_copy = tumor_types.copy()
                sample_types.append(tumor_copy)
            
            elif old_seer == '37000':
                tumor_types.update({"pmid": publication})
                tumor_types.update({"sample_types": {"id": "NCIT:C3262",
                                    "label": "Neoplasm",
                                    "counts": counts}
                                    })
                tumor_copy = tumor_types.copy()
                sample_types.append(tumor_copy)
                    
        else:
            info = converted[publication]
            icdo = info[0]
            old_seer = info[1]
            counts = info[2]
            
            tumor_types.update({"pmid": publication})
            tumor_types.update({"sample_types": {"id": 'CL497885', 
                                                 "label": f'Unknown primary site for ICD-O {icdo}',
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
    to_convert = cl.find({'cancertype': {'$exists': True}}) 
    converted = converter(to_convert)
    new_annotations = make_ncit_annotation(converted)  
    
   # Rename 'cancertype' field to 'sample_types' for all the publications in the collection:
    cl.updateMany({'cancertype': {'$exists': True}}, {'$rename': {'cancertype': 'sample_types'}})
    
    # Update 'sample_type' annotations with the new NCIt annotations:
    print("\n...Updating sample type annotations on progenetix.publications...\n")
    for post in new_annotations:  
        cl.update_one({'id': post['pmid']}, {'$set': {'sample_types': post['sample_types']}})
        print(f'Updated tumor type annotation for the publication with "id" {post["pmid"]}.')        
        

##############################################################################

if __name__ == '__main__':
    main()

##############################################################################
##############################################################################
##############################################################################

