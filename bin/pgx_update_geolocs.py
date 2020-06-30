#!/usr/local/bin/python3

import sys, yaml
from os import path as path
import argparse
from pymongo import MongoClient
from pyexcel import get_sheet
from progress.bar import IncrementalBar

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *
from pgy import *

"""podmd

This script provides a number of update & normalization functions for geographic
attributes, such as

* ISO country codes
* (TBD)

It uses an input file with the ISO-3166-alpha2 and ISO-3166-alpha3 country
codes, and has the options to:

* map the `-3` codes into our `geolocs` database (where city point locations are
stored with attached ISO-3166-alpha2 codes)
* add/update the ISO-3166-alpha3 codes for `provenance.geo` objects in
`biosamples` and `publications`, based on the _correctly spelled_ country names

podmd"""

################################################################################
################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--geoisofile", help="file with ISO-3166-alpha3 geographic codes and country names")
    args = parser.parse_args()

    return(args)

################################################################################

def main():

    with open( path.join( path.abspath( dir_path ), '..', "config", "defaults.yaml" ) ) as cf:
        config = yaml.load( cf , Loader=yaml.FullLoader)
    config[ "paths" ][ "module_root" ] = path.join( path.abspath( dir_path ), '..' )
    config[ "paths" ][ "out" ] = path.join( config[ "paths" ][ "module_root" ], "data", "out" )

    config[ "dataset_ids" ] = [ "progenetix", "arraymap" ]

    config[ "iso_reset" ] = True

    args = _get_args()

    if not  path.isfile( args.geoisofile ):
        print("No geoisofile file was provided with -g ...")
        sys.exit()

    table = get_sheet(file_name=args.geoisofile)

    header = table[0]
    col_inds = { }
    hi = 0
    for col_name in header:
        if col_name in ("ISO-3166-alpha2", "ISO-3166-alpha3", "country"):
            col_inds[ col_name ] = hi
        hi += 1

    ############################################################################

    if confirm_prompt("Update geolocs codes from File?", False):
        print("=> updating geolocs DB")
        _update_geolocs_db(config, table, col_inds)

    if confirm_prompt("Update geo codes in biosamples?", False):
        print("=> updating biosamples DBs")
        _update_biosamples_geolocs(config, table, col_inds)

    if confirm_prompt("Update geo codes in publications?", False):
        print("=> updating publications DB")
        _update_publications_geolocs(config, table, col_inds)

################################################################################
################################################################################
################################################################################

def _update_geolocs_db(config, table, col_inds):

    mongo_client = MongoClient( )
    geo_coll = mongo_client[ "progenetix" ][ "geolocs" ]
    geo_all = geo_coll.count_documents({})

    bar = IncrementalBar('geolocs', max = geo_all)

    g_i = 0

    for i in range(1, len(table)):
        if not table[ i, col_inds[ "ISO-3166-alpha2" ] ]:
            break

        query = { "ISO-3166-alpha2": table[ i, col_inds[ "ISO-3166-alpha2" ] ] }
        for geoloc in geo_coll.find(query):
            # print(("{}, {}: {} - {}").format(geoloc["city"], geoloc["country"], geoloc["ISO-3166-alpha2"], table[ i, col_inds[ "ISO-3166-alpha3" ] ]))
            geo_coll.update_one( { "_id" : geoloc[ "_id" ] }, { "$set": { "ISO-3166-alpha3": table[ i, col_inds[ "ISO-3166-alpha3" ] ], "country": table[ i, col_inds[ "country" ] ] } } )
            g_i += 1
            bar.next()

    bar.finish()
    print(("{} locations were updated in geolocs").format(g_i))

################################################################################

def _update_biosamples_geolocs(config, table, col_inds):

    mongo_client = MongoClient( )
    g_i = 0

    for ds_id in config[ "dataset_ids" ]:
        bios_coll = mongo_client[ ds_id ][ "biosamples" ]

        bio_all = bios_coll.count_documents({})

        bar = IncrementalBar(ds_id+' biosamples', max = bio_all)

        if config[ "iso_reset" ]:
            bios_coll.update_many( { }, { "$set": { "provenance.geo.ISO-3166-alpha3": "XXX" } } )

        bios_coll.update_many( { "provenance.geo.country": "South Korea" }, { "$set": { "provenance.geo.country": "Republic of Korea" } } )

        for i in range(1, len(table)):
            if not table[ i, col_inds[ "ISO-3166-alpha2" ] ]:
                break

            query = { "provenance.geo.country": table[ i, col_inds[ "country" ] ] }
            for bios in bios_coll.find(query):
                bios_coll.update_one( { "_id" : bios[ "_id" ] }, { "$set": { "provenance.geo.ISO-3166-alpha3": table[ i, col_inds[ "ISO-3166-alpha3" ] ] } } )
                g_i += 1
                bar.next()
        
        bar.finish()
        print(("{} locations were updated in {}.biosamples").format(g_i, ds_id))
        g_i = 0

    g_i = 0

################################################################################

def _update_publications_geolocs(config, table, col_inds):

    mongo_client = MongoClient( )
    pub_coll = mongo_client[ "progenetix" ][ "publications" ]
    g_i = 0

    if config[ "iso_reset" ]:
        pub_coll.update_many( { }, { "$set": { "provenance.geo.ISO-3166-alpha3": "XXX" } } )

    pub_coll.update_many( { "provenance.geo.country": "South Korea" }, { "$set": { "provenance.geo.country": "Republic of Korea" } } )

    for i in range(1, len(table)):
        if not table[ i, col_inds[ "ISO-3166-alpha2" ] ]:
            break

        query = { "provenance.geo.country": table[ i, col_inds[ "country" ] ] }
        for pub in pub_coll.find(query):
            pub_coll.update_one( { "_id" : pub[ "_id" ] }, { "$set": { "provenance.geo.ISO-3166-alpha3": table[ i, col_inds[ "ISO-3166-alpha3" ] ] } } )
            g_i += 1

    print("{} locations were updated in publications".format(g_i))

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main(  )
