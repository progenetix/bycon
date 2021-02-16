#!/usr/local/bin/python3

import re, argparse
import datetime, time
import sys, base36
import json
import pandas as pd
from pymongo import MongoClient
import random
from os import path, environ, pardir
from progressbar import Bar
from pydoc import locate
from jsonschema import validate

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from bycon.lib.read_specs import *
from services.lib.table_tools import *

"""
## `newSampleInserter`

"""

################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--test', help='No. of samples for test run')
    parser.add_argument('-d', '--output_db', help='the database to write into.')
    parser.add_argument('-s', '--source', help='which repo is input data from')
    args = parser.parse_args()

    return(args)

################################################################################

def main():

    curr_time = datetime.datetime.now()
    configs = ["inserts", "datatables"]

    byc = {
        "pkg_path": pkg_path,
        'args': _get_args(),
        "errors": [ ],
        "warnings": [ ]
    }

    # first pre-population w/ defaults
    for config in configs:
        these_prefs = read_local_prefs( config, dir_path )
        for d_k, d_v in these_prefs.items():
            byc.update( { d_k: d_v } )

    if not byc['args'].source in byc['data_sources']:
        print( 'Does not recognize data source!')

    # TODO: check for import_path
    # TODO: check for dataset => if not byc['args'].output_db in byc["config"][ "dataset_ids" ]:
    # ... prompt for continuation w/ Q "new dataset ??? etc."

################################################################################

    ### read in meta table
    metapath = byc['import_path']
    mytable = pd.read_csv(metapath, sep = '\t', dtype = str)
    mytable = mytable.where((pd.notnull(mytable)), None) ## convert pd.nan to None

    ### define list/dictionary of objects to insert in 4 collections
    variants_list = []
    callsets_dict = {}
    biosamples_dict = {}
    individuals_dict = {}

    ### find all existing ids in each output database and collections.
    exist_callset_id = {}
    exist_biosample_id = {}
    exist_individual_id  = {}

    mongo_client = MongoClient( )

    ds_id = byc['args'].output_db
    data_db = mongo_client[ds_id]
    exist_callset_id[ds_id] = data_db.callsets.distinct('info.legacy_id')
    exist_biosample_id[ds_id] = data_db.biosamples.distinct('info.legacy_id')
    exist_individual_id[ds_id] = data_db.individuals.distinct('info.legacy_id')

    no_row = mytable.shape[0]
   
    if byc['args'].test:
        test = int(byc['args'].test)
        bar_length = test
        rdm_row = random.sample(range(no_row), test)
        mytable = mytable.iloc[rdm_row, :]
        print( f"TEST MODE for {test} of samples.")
    else:
        bar_length = no_row

    bar = Bar("Reading in metadata table", max = bar_length, suffix="%(percent)d%%"+" of "+str(bar_length) )
    for row in mytable.itertuples():

        if row.loc['status'].startswith('excluded'):
            continue

        ### assign variables from info fields
        
        info_field = {}
        column_names = io_table_header( **byc )
        field_to_db = io_map_to_db( **byc )
        bs = 'biosamples'
        cs = 'callsets'
        ind = 'individuals'
        for field in column_names:
            if field in row:
                if field in field_to_db:
                    info_field[field_to_db[field][0]][field] = row.loc[field]
                else:
                    info_field[field] = row.loc[field]
                
        if byc['args'].source == 'arrayexpress':
            info_field['uid'] = 'AE-'+ info_field['experiment'].replace('E-','').replace('-','_') + '-' +\
                info_field['uid'].replace("-", "_").replace(' ', '_').replace('.CEL','') + '-' +\
                byc['platform_rename'][info_field['platform_id']]  ## initial rename 
        
        # TODO: default should **not** be blood but rather icdot-C76.9: ill-defined 
        if not info_field[bs]['icdot::id']:
            info_field[bs]['icdot::id'] = 'C42.0'
        if not info_field[bs]['icdot::label']:
            info_field[bs]['icdot::label'] = 'Blood'

        if info_field[bs]['icdom::id']:
            info_field[bs]['icdom::id'] = info_field[bs]['icdom::id'].replace('/','')
        else:
            info_field[bs]['icdom::id'] = '00000'
            info_field[bs]['icdom::label'] = 'Normal'
        
        if not 'description' in info_field:
                info_field[bs]['description'] = ''

        if 'age_iso' not in info_field[bs] and info_field['age']:
            try:
                # TODO: separate method; also e.g. using a split or regex after stringify
                age = int(info_field['age'])
                info_field[bs]['age_iso'] = 'P'+str(v)+'Y'
            except ValueError:
                age = float(info_field['age'])
                rem_age = age - int(age)
                info_field[bs]['age_iso'] = 'P'+str(int(age)) +'Y'+ str(round(rem_age*12)) + 'M' 

        if 'PATO::id' not in info_field[ind] and info_field['sex']:
            sex = info_field['sex'].lower()
            if sex == 'female':
                info_field[ind]['PATO::id'] = 'PATO:0020002'
                info_field[ind]['PATO::label'] = 'female genotypic sex'
            elif sex == 'male':
                info_field[ind]['PATO::id'] = 'PATO:0020001'  
                info_field[ind]['PATO::label'] = 'male genotypic sex'
        
        ### derived attributes that are shared by collections
        info_field[bs]['legacy_id'] = 'PGX_AM_BS_' + info_field['uid']
        info_field[cs]['legacy_id'] = 'pgxcs::{}::{}'.format(info_field['experiment'], info_field['uid'])
        info_field[ind]['legacy_id'] = 'PGX_IND_' + info_field['uid']

        info_field[bs]['id'] = _generate_id('pgxbs')
        info_field[cs]['id'] = _generate_id('pgxcs')
        info_field[cs]['biosample_id'] = info_field[bs]['id']
        info_field[ind]['id'] = _generate_id('pgxind')
        info_field[bs]['individual_id'] = info_field[ind]['id']

        info_field[bs]['EFO::id'] = 'EFO:0009654' if info_field[bs]['icdom::id'] == '00000' else 'EFO:0009656'
        info_field[bs]['EFO::label'] = 'reference sample' if info_field[bs]['icdom::id'] == '00000' else 'neoplastic sample'
        info_field[ind]['NCBITaxon::id'] = 'NCBITaxon:9606'
        info_field[ind]['NCBITaxon::label'] = 'Homo sapiens'
        for collection in [bs, cs, ind]:
            info_field[collection]['DUO::id'] = 'DUO:0000004'
            info_field[collection]['DUO::label'] = 'no restriction'

        ############################
        ##   variants & callsets  ##
        ############################
        variants, callset  = _initiate_vs_cs(byc['json_file_root'], info_field['experiment'], info_field['uid'])

        ## variants
        for variant in variants:
            variant['callset_id'] = info_field[cs]['id']
            variant['biosample_id'] = info_field[bs]['id']
            variant['updated'] = curr_time

        variants_list.append(variants)

        ## callsets
        for k,v in info_field[cs].items():
            db_key, attr_type = field_to_db['.'.join([cs,k])]
            assign_nested_value(callset, db_key, locate(attr_type)(v))

        if info_field['platform_id']:
            callset['description'] = _retrievePlatformLabel(mongo_client, info_field['platform_id'])
        
        callsets_dict[info_field[cs]['legacy_id']] = callset

        ############################
        ######   biosamples  #######
        ############################

        biosample= {
                    'updated': curr_time,
                    }
        
        if byc['args']['source'] == 'arrayexpress':
            info_field[bs][bs+'.'+'arrayexpress::id'] = 'arrayexpress:'+ info_field['experiment'],
            biosample['project_id'] = 'A' + info_field['experiment']
        
        for k,v in info_field[bs].items():
            db_key, attr_type = field_to_db['.'.join([bs,k])]
            assign_nested_value(biosample, db_key, locate(attr_type)(v))
                
        biosamples_dict[info_field[bs]['legacy_id']] = biosample

        ############################
        ######   individuals  ######
        ############################

        individual = {
                        'updated': curr_time
                     }

        for k,v in info_field[ind].items():
            db_key, attr_type = field_to_db['.'.join([ind,k])]
            assign_nested_value(individual, db_key, locate(attr_type)(v))
        individuals_dict[info_field[ind]['legacy_id']] = individual

        bar.next()
    bar.finish()

    ############################
    ###   database write-in  ###
    ############################

    confirm = input("""Processed {} variants, {} callsets, {} biosamples and {} individuals for update.
Do you want to continue? [y/n]""".format(sum([len(v) for v in variants_list]), len(callsets_dict), len(biosamples_dict),
                     len(individuals_dict)))
    update = input("""In case of existing record (matching info.legacy_id). Do you want to update? [y/n] """)
    if confirm == 'y':

        for variant_obj in variants_list:
            try:
                data_db.variants.insert_many(variant_obj)
            except TypeError:
                pass

        for callset_id_leg, callset_obj in callsets_dict.items():
            if (not update) and (callset_id_leg in exist_callset_id[ds_id]):
                continue
            data_db.callsets.insert_one(callset_obj)

        for biosample_id_leg, biosample_obj in biosamples_dict.items():
            if (not update) and (biosample_id_leg in exist_biosample_id[ds_id]):
                continue
            data_db.biosamples.insert_one(biosample_obj)

        for individual_id_leg, individual_obj in individuals_dict.items():
            if (not update) and (individual_id_leg in exist_individual_id[ds_id]):
                continue
            data_db.individuals.insert_one(individual_obj)



################################################################################
################################################################################

def _generate_id(prefix):
    time.sleep(.001)
    return '{}-{}'.format(prefix, base36.dumps(int(time.time() * 1000))) ## for time in ms

################################################################################

def _initiate_vs_cs(rootdir, ser, arr):

    ## variant collections
    # TODO: use path.join(  )
    with open('{0}/{1}/{2}/variants.json'.format(rootdir,ser,arr),'r') as json_data:
        variants_json = json.load(json_data)

    variant_obj = []

    for v in variants_json:

        v.pop('no', None)
        v['info']['cnv_value'] = v['info'].pop('value')
        v['info']['var_length'] = v['info'].pop('svlen')
        v['info'].pop('probes', None)
        v['variantset_id'] = 'AM_VS_GRCH38'

        variant_obj.append(v)

    ## callset collections
    # TODO: use path.join(  )
    with open('{0}/{1}/{2}/callset.json'.format(rootdir,ser,arr),'r') as json_data:
        callset_json = json.load(json_data)

    callset_json.pop('callset_id', None)
    callset_obj = callset_json

    return variant_obj, callset_obj

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
