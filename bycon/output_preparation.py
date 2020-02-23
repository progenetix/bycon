from pymongo import MongoClient
import re

########################################################################################################################
########################################################################################################################
########################################################################################################################


def plotpars_from_args(opts, **kwargs):

    plot_pars = { }
    plot_pars["dotalpha"] = 0.2

    for opt, arg in opts:
        if opt in ("-a", "--dotalpha"):
            plot_pars[ "dotalpha" ] = arg

    return plot_pars

########################################################################################################################

def callsets_add_metadata(cs, **kwargs):

    dataset_id = kwargs[ "data_pars" ][ "dataset_id" ]
    bio_prefixes = kwargs[ "config" ][ "bio_prefixes" ]

    mongo_client = MongoClient( )
    mongo_db = mongo_client[ dataset_id ]
    mongo_coll = mongo_db[ 'biosamples' ]
    
    for bio_pre in bio_prefixes:
        cs[bio_pre] = ""

    bios = mongo_coll.find_one({"id": cs["biosample_id"] })

    if bios:
        for biocharacteristic in bios["biocharacteristics"]:
            for bio_pre in bio_prefixes:
                if re.compile( '^'+bio_pre ).match(biocharacteristic["type"]["id"]):
                    cs[ bio_pre ] = biocharacteristic["type"]["id"]
    return cs

########################################################################################################################

