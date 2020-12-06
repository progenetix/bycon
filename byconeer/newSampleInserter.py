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
"""

## `newSampleInserter`

"""

################################################################################

def main():

    service = "inserts"

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
    these_prefs = read_local_prefs( service, dir_path )
    for d_k, d_v in these_prefs.items():
        byc.update( { d_k: d_v } )

    if not byc['args'].source in byc['data_sources']:
        print( 'Does not recognize data source!')

################################################################################

    ### read in meta table
    mytable = pd.read_csv(byc['meta_path'], sep = '\t', dtype = {k: str for k in byc['str_type_columns']})
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
         

        ### assign variables from info fields
        status, ser, arr, plf, icdt, icdtc, icdm, icdmc, ncidcode, ncitterm, diagnosis, age, sex, pmid, tnm, city, country, cellline_id, cellosaurus_id = \
                  [row.loc[column_name] for column_name in byc['column_names']]

        if status.startswith('excluded'):
            continue

        if byc['args'].source == 'arrayexpress':
            arr = 'AE-'+ ser.replace('E-','').replace('-','_') + '-' +\
                arr.replace("-", "_").replace(' ', '_').replace('.CEL','') + '-' +\
                byc['platform_rename'][plf]  ## initial rename 
           
        if not icdtc:
                icdtc = 'C42.0'
                icdt = 'Blood'

        if icdmc:
            icdmc = icdmc.replace('/','')
        else:
            icdmc = '00000'
            icdm = 'Normal'
        
        if not diagnosis:
                diagnosis = ''

        if age:  
            if type(age) == str:
                age = re.sub('[A-Za-z _]','',age)
            
            try:
                age = int(age)
                isoage = 'P'+str(age)+'Y'
            except ValueError:
                age = float(age)
                rem_age = age - int(age)
                isoage = 'P'+str(int(age)) +'Y'+ str(round(rem_age*12)) + 'M' 

        if sex:
            sex = sex.lower()
            if sex == 'male':
                sex_id = 'PATO:0020001'  
                sex_label = 'male genotypic sex'

            if sex == 'female':
                sex_id = 'PATO:0020002'
                sex_label = 'female genotypic sex'
        else:
            sex_id = sex_label = None

        ### derived attributes that are shared by collections
        biosample_id_leg = 'PGX_AM_BS_' + arr
        callset_id_leg = 'pgxcs::{}::{}'.format(ser, arr)
        individual_id_leg = 'PGX_IND_' + arr

        biosample_id = generate_id('pgxbs')
        callset_id = generate_id('pgxcs')
        individual_id = generate_id('pgxind')
        material_id = 'EFO:0009654' if icdmc == '00000' else 'EFO:0009656'
        material_label = 'reference sample' if icdmc == '00000' else 'neoplastic sample'
        geo_provenance = _retrieveGEO(mongo_client, city, country)
        data_use = {
                'label' : 'no restriction',
                'id' : 'DUO:0000004'
                }

        ############################
        ##   variants & callsets  ##
        ############################
        variants, callset  = _initiate_vs_cs(byc['json_file_root'], ser, arr)

        ### check if callset_id exists already in the dababase and in the current process.

        check_callset = [callset_id in exist_callset_id[db_name] for db_name in output_db]
        
        if all(check_callset):
            continue ### if callset exists then the sample shouldn't be processed.

        ## variants
        for variant in variants:
            variant['callset_id'] = callset_id
            variant['biosample_id'] = biosample_id
            variant['updated'] = retrieveTime(metapath, 'str')

        variants_list.append(variants)

        ## callsets
        callset['id'] = callset_id
        callset['biosample_id'] = biosample_id
        callset['updated'] = retrieveTime(metapath, 'date')
        callset['info']['legacy_id'] = callset_id_leg
        if plf:
            callset['description'] = _retrievePlatformLabel(mongo_client, plf)
        else:
            callset['description'] = plf_text
        callset['data_use_conditions'] = data_use

        # if age:
        #     callset['info']['isoage'] = isoage
        #     callset['info']['age_years'] = age

        if sex:
            callset['info']['PATO'] = {
                                        'id': sex_id,
                                        'label': sex_label
                                        }
        callsets_dict[callset_id_leg] = callset

        ############################
        ######   biosamples  #######
        ############################

        biosample= {
                'id': biosample_id,
                'description': diagnosis,
                'biocharacteristics':[
                        {
                                'type': {
                                        'id':  'icdot-' + icdtc,
                                        'label': icdt
                                },
                        },
                        {
                                'type': {
                                        'id':  'icdom-' + icdmc,
                                        'label': icdm
                                 }
                                }
                        ],
                'updated': retrieveTime(metapath, 'date'),
                'individual_id': individual_id,
                'project_id': 'A' + ser,
                'provenance':{
                        'material':{
                                'type':{
                                        'id': material_id,
                                        'label': material_label
                                        }
                                },
                        'geo': geo_provenance
                        },
                'info':{
                        'death': None,
                        'followup_months': None,
                        'legacy_id': biosample_id_leg
                        # 'samplesource': samplesource
                        },
                'data_use_conditions': data_use

                }
        if byc['args']['source'] == 'arrayexpress':
            biosample['external_references'] =[
                                                {
                                                        'type': {
                                                                'id': 'arrayexpress:'+ ser,
                                                        }
                                                },
                        ]
        elif byc['args']['source'] == 'geo':
            biosample['external_references'] =[
                                                {
                                                        'type': {
                                                                'id': 'geo:' + ser,
                                                        }
                                                },
                                                {
                                                        'type':{
                                                                'id': 'geo:' + arr,
                                                        }
                                                },
                                                {
                                                        'type': {
                                                                'id': 'geo:' + plf,
                                                        }
                                                }
                                                ]

        if ncitcode:
            biosample['biocharacteristics'].append(
                                               {
                                                'type': {
                                                        'id':  'NCIT:' + ncitcode.capitalize(),
                                                        'label': ncitterm
                                                 }
                                                }
                                                )
                                
        if age:
            biosample['individual_age_at_collection'] = {
                    
                                            'age_class': ### to be added later
                                                {
                                                        'id': None,
                                                        'label': None
                                                    },
                                            'age': isoage
                                            }
                
        if tnm:
            biosample['info']['tnm'] = tnm

        if plf:
            biosample['external_references'].append(
                    {
                                'type': {
                                        'id': 'geo:' + plf,
                                }
                    })

        if pmid:
            biosample['external_references'].append(
                    {
                                'type': {
                                        'id': 'PMID:' + pmid,
                                        'relation': 'pubmed'
                                }
                    })

        if cellosaurus_id:
            biosample['external_references'].append(
                    {
                                'type':{
                                        'id': 'cellosaurus:' + cellosaurus_id,
                                
                                        'relation': 'cellosaurus'
                                }
                    })  

        if cellline_id:
            biosample['info']['cell_line'] = cellline_id

        biosamples_dict[biosample_id_leg] = biosample

        ############################
        ######   individuals  ######
        ############################

        individual = {
                'id': individual_id,
                'description': None,
                'biocharacteristics':[
                        {
                                'description': sex,

                                'type': {
                                        'id': sex_id,
                                        'label': sex_label}
                                },
                        {
                                'description': None,
                                'type':{
                                        'id' : 'NCBITaxon:9606',
                                        'label' : 'Homo sapiens'
                                }
                        }],
                 'data_use_conditions' : data_use,
                 'geo_provenance': geo_provenance,
                 'updated': retrieveTime(metapath, 'date'),
                 'info': {'legacy_id': individual_id_leg}
                }

        individuals_dict[individual_id_leg] = individual

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
            if callset_id in exist_callset_id[db_name]:
                continue
            data_db.callsets.insert_one(callset_obj)

        for biosample_id_leg, biosample_obj in biosamples_dict.items():
            if biosample_id in exist_biosample_id[db_name]:
                continue
            data_db.biosamples.insert_one(biosample_obj)

        for individual_id_leg, individual_obj in individuals_dict.items():
            if individual_id in exist_individual_id[db_name]:
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
        pass

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
