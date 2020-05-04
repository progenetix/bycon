#!/usr/local/bin/python3

import sys, yaml
from os import path as path
import argparse
from pymongo import MongoClient
from pyexcel import get_sheet

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *

################################################################################
################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--geoisofile", help="file with iso 3166 geographic codes and country names")
    args = parser.parse_args()

    return(args)

################################################################################

def main():

    with open( path.join( path.abspath( dir_path ), '..', "config", "defaults.yaml" ) ) as cf:
        config = yaml.load( cf , Loader=yaml.FullLoader)
    config[ "paths" ][ "module_root" ] = path.join( path.abspath( dir_path ), '..' )
    config[ "paths" ][ "out" ] = path.join( path.abspath( dir_path ), '..', "data", "out" )

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
            print(col_name+": "+str(hi))
            col_inds[ col_name ] = hi
        hi += 1

    mongo_client = MongoClient( )
    geo_coll = mongo_client[ "progenetix" ][ "geolocs" ]

    g_i = 0

    for i in range(1, len(table)):
        if not table[ i, col_inds[ "ISO-3166-alpha2" ] ]:
            break

        print(str(i)+": "+table[ i, col_inds[ "country" ] ])
        query = { "ISO-3166-alpha2": table[ i, col_inds[ "ISO-3166-alpha2" ] ] }
        for geoloc in geo_coll.find(query):
            print(("{}, {}: {} - {}").format(geoloc["city"], geoloc["country"], geoloc["ISO-3166-alpha2"], table[ i, col_inds[ "ISO-3166-alpha3" ] ]))
            geo_coll.update_one( { "_id" : geoloc[ "_id" ] }, { "$set": { "ISO-3166-alpha3": table[ i, col_inds[ "ISO-3166-alpha3" ] ], "country": table[ i, col_inds[ "country" ] ] } } )
            g_i += 1

    print(("{} locations were updated").format(g_i))


################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main(  )
