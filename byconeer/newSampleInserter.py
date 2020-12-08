#!/usr/local/bin/python3

import re, argparse
import datetime, time
import sys, base36
import json
import pandas as pd
from pymongo import MongoClient
import random
from os import path, environ, pardir
from progress.bar import Bar

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from bycon.lib.read_specs import *
from bycon.lib.table_tools import *

"""

## `newSampleInserter`

"""

################################################################################

def main():

    configs = ["inserts", "datatables"]

    byc = {
        "pkg_path": pkg_path,
        "config": read_bycon_configs_by_name( "defaults" ),
        'args': _get_args(),
        "errors": [ ],
        "warnings": [ ]
    }

    for d in [
        "dataset_definitions",
        "filter_definitions"
    ]:
        byc.update( { d: read_bycon_configs_by_name( d ) } )

    # first pre-population w/ defaults
    for config in configs:
        these_prefs = read_local_prefs( config, dir_path )
        for d_k, d_v in these_prefs.items():
            byc.update( { d_k: d_v } )

    if not byc['args'].source in byc['data_sources']:
        print( 'Does not recognize data source!')

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

    db_name = byc['args'].output_db
    data_db = mongo_client[db_name]
    exist_callset_id[db_name] = data_db.callsets.distinct('info.legacy_id')
    exist_biosample_id[db_name] = data_db.biosamples.distinct('info.legacy_id')
    exist_individual_id[db_name] = data_db.individuals.distinct('info.legacy_id')

    metafile_time = retrieveTime(metapath, 'date')

    no_row = mytable.shape[0]
   
    if byc['args'].test:
        test = int(byc['args'].test)
        bar_length = test
        rdm_row = random.sample(range(no_row), test)
        mytable = mytable.iloc[rdm_row, :]
        print( "¡¡¡ TEST MODE - no db update !!!")
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
                age = int(info_field['age'])
                info_field[bs]['age_iso'] = 'P'+str(v)+'Y'
            except ValueError:
                age = float(info_field['age'])
                rem_age = age - int(age)
                info_field[bs]['age_iso'] = 'P'+str(int(age)) +'Y'+ str(round(rem_age*12)) + 'M' 

        if 'PATO::id' not in info_field[ind] and info_field['sex']:
            sex = info_field['sex'].lower()
            if sex == 'male':
                info_field[ind]['PATO::id'] = 'PATO:0020001'  
                info_field[ind]['PATO::label'] = 'male genotypic sex'

            if sex == 'female':
                info_field[ind]['PATO::id'] = 'PATO:0020002'
                info_field[ind]['PATO::label'] = 'female genotypic sex'
        
        ### derived attributes that are shared by collections
        info_field[bs]['legacy_id'] = 'PGX_AM_BS_' + info_field['uid']
        info_field[cs]['legacy_id'] = 'pgxcs::{}::{}'.format(info_field['experiment'], info_field['uid'])
        info_field[ind]['legacy_id'] = 'PGX_IND_' + info_field['uid']

        info_field[bs]['id'] = generate_id('pgxbs')
        info_field[cs]['id'] = generate_id('pgxcs')
        info_field[ind]['id'] = generate_id('pgxind')
        info_field[bs]['EFO::id'] = 'EFO:0009654' if info_field[bs]['icdom::id'] == '00000' else 'EFO:0009656'
        info_field[bs]['EFO::label'] = 'reference sample' if info_field[bs]['icdom::id'] == '00000' else 'neoplastic sample'
        info_field[ind]['NCBITaxon::id'] = 'NCBITaxon:9606'
        info_field[ind]['NCBITaxon::label'] = 'Homo sapiens'
                
        geo_provenance = {
                        { 'label': info_field[bs]['geoprov_label'],
                        'precision': info_field[bs]['geoprov_precision'],
                        'city': info_field[bs]['geoprov_city'],
                        'country': info_field[bs]['geoprov_country'],
                        'latitude': info_field[bs]['latitude'],
                        'longitude': info_field[bs]['longitude'],
                        'geojson': {
                                    'type': 'Point',
                                    'coordinates': [
                                        info_field[bs]['longitude'],
                                        info_field[bs]['latitude']
                                    ]
                                },
                        'ISO-3166-alpha3': iso_country
                        }   
                        }
        data_use = {
                'label' : 'no restriction',
                'id' : 'DUO:0000004'
                }

        ############################
        ##   variants & callsets  ##
        ############################
        variants, callset  = _initiate_vs_cs(byc['json_file_root'], ser, arr)

        ### check if callset_id exists already in the dababase and in the current process.
        
        if callset_id in exist_callset_id[db_name]:
            continue ### if callset exists then the sample shouldn't be processed.

        ## variants
        for variant in variants:
            variant['callset_id'] = info_field[cs]['id']
            variant['biosample_id'] = info_field[bs]['id']
            variant['updated'] = metafile_time

        variants_list.append(variants)

        ## callsets
        for k,v in info_field[cs].items():
            assign_nested_value(callset, field_to_db['.'.join([cs,k])][1], v)
        if info_field['platform_id']:
            callset['description'] = _retrievePlatformLabel(mongo_client, info_field['platform_id'])
        callset['data_use_conditions'] = data_use
        
        callsets_dict[info_field[cs]['legacy_id']] = callset

        ############################
        ######   biosamples  #######
        ############################

        biosample= {
                    'updated': metafile_time,
                    'data_use_conditions': data_use
                    }
        
        if byc['args']['source'] == 'arrayexpress':
            info_field[bs][bs+'.'+'arrayexpress::id'] = 'arrayexpress:'+ info_field['experiment'],
            biosample['project_id'] = 'A' + info_field['experiment']
        
        for k,v in info_field[bs].items():
            assign_nested_value(biosample, field_to_db['.'.join([bs,k])][1], v)
                
        biosamples_dict[info_field[bs]['legacy_id']] = biosample

        ############################
        ######   individuals  ######
        ############################

        individual = {
                'id': info_field[ind]['id'],
                'data_use_conditions' : data_use,
                'geo_provenance': geo_provenance,
                 'updated': metafile_time
                 }

                
                
                

                 'info': {'legacy_id': info_field[ind]['legacy_id']}
                }

        individuals_dict[info_field[ind]['legacy_id']] = individual

        bar.next()
    bar.finish()

    ############################
    ###   database write-in  ###
    ############################

    confirm = input("""I have processed {} variants, {} callsets, {} biosamples and {} individuals for update.
Do you want to continue? [y/n]""".format(sum([len(v) for v in variants_list]), len(callsets_dict), len(biosamples_dict),
                     len(individuals_dict)))

    if confirm == 'y':

        for variant_obj in variants_list:
            try:
                data_db.variants.insert_many(variant_obj)
            except TypeError:
                pass

        for callset_id_leg, callset_obj in callsets_dict.items():
            if callset_id_leg in exist_callset_id[db_name]:
                continue
            data_db.callsets.insert_one(callset_obj)

        for biosample_id_leg, biosample_obj in biosamples_dict.items():
            if biosample_id_leg in exist_biosample_id[db_name]:
                continue
            data_db.biosamples.insert_one(biosample_obj)

        for individual_id_leg, individual_obj in individuals_dict.items():
            if individual_id_leg in exist_individual_id[db_name]:
                continue
            data_db.individuals.insert_one(individual_obj)

################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--test', help='No. of samples for test run')
    parser.add_argument('-d', '--output_db', help='the database to write into.')
    parser.add_argument('-s', '--source', help='which repo is input data from')
    args = parser.parse_args()

    return(args)

def generate_id(prefix):
    time.sleep(.001)
    return '{}-{}'.format(prefix, base36.dumps(int(time.time() * 1000))) ## for time in ms


def retrieveTime(filename, return_type):
    time = datetime.datetime.now()
    if return_type == 'str':
        return time.isoformat()
    elif return_type == 'date':
        return time

################################################################################
################################################################################

def _initiate_vs_cs(rootdir, ser, arr):

    ## variant collections
    with open('{0}/{1}/{2}/variants.json'.format(rootdir,ser,arr),'r') as json_data:
        variants_json = json.load(json_data)

    variant_obj = []

    for v in variants_json:

        v.pop('no', None)
        v['info']['cnv_value'] = v['info'].pop('value')
        v['info']['cnv_length'] = v['info'].pop('svlen')
        v['info'].pop('probes', None)
        v['variantset_id'] = 'AM_VS_GRCH38'

        variant_obj.append(v)


    ## callset collections
    with open('{0}/{1}/{2}/callset.json'.format(rootdir,ser,arr),'r') as json_data:
        callset_json = json.load(json_data)

    callset_json.pop('callset_id', None)
    callset_obj = callset_json

    return variant_obj, callset_obj

def _retrieveGEO(client, city, country):
    cl = client['progenetix'].geolocs
    geo_obj = cl.find_one({'$and':[{'city':city},{'country':country}]})
    if geo_obj:
        geoPrecision = 'city'
        country = geo_obj['country']
        geoLabel = city + ', ' + country
        geojson = geo_obj['geojson']
        [geolong, geolat] = geojson['coordinates']
        geoLabel = city + ', ' + country
        try:
            iso_country = geo_obj['ISO-3166-alpha3']
        except KeyError:
            iso_country = None

    else:
        print(city)
        geoLabel = None
        geoPrecision = None
        city = None
        country = None
        geolat = None
        geolong = None
        geojson = None
        iso_country = None
        
    geo_info = { 'label': geoLabel,
            'precision': geoPrecision,
            'city': city,
            'country': country,
            'latitude': geolat,
            'longitude': geolong,
            'geojson': geojson,
            'ISO-3166-alpha3': iso_country
            }

    return geo_info

def _retrievePlatformLabel(client, platformID):
    cl = client['arraymap'].platforms
    plf_obj = cl.find_one({'PLATFORMID':platformID})
    try:
        return plf_obj['PLATFORMLABEL']
    except:
        print('{} has no platform description in arraymap.platforms'.format(platformID))
        return None

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
