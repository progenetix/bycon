from pymongo import MongoClient
from os import path as path
from datetime import datetime, date
from progress.bar import IncrementalBar
import re, yaml, json
from isodate import parse_duration
from .tabulating_tools import *


def pgx_populate_callset_info( **kwargs ):

    """podmd
 
    ### Denormalizing Progenetix data

    While the Progenetix data schema is highly flexible, the majority of
    database content can be expressed with a limited set of parameters.

    The `pgx_populate_callset_info` method denormalizes the main information
    from the `biosamples` collection into the corresponding `callsets`, using
    the schema-free `info` object.

    podmd"""

    mongo_client = MongoClient( )
    mongo_db = mongo_client[ kwargs[ "dataset_id" ] ]
    bios_coll = mongo_db[ "biosamples" ]
    inds_coll = mongo_db[ "individuals" ]
    cs_coll = mongo_db[ "callsets" ]

    filter_defs = kwargs[ "filter_defs" ]

    cs_query = { }
    cs_count = cs_coll.estimated_document_count()

    bar = IncrementalBar('callsets', max = cs_count)

    for cs in cs_coll.find( { } ):

        update_flag = 0
        if not "info" in cs.keys():
            cs[ "info" ] = { }

        bios = bios_coll.find_one({"id": cs["biosample_id"] })
        inds = inds_coll.find_one({"id": bios["individual_id"] })

        if not "biocharacteristics" in inds:
            inds[ "biocharacteristics" ] = [ ]

        prefixed = [ *bios[ "biocharacteristics" ], *bios[ "external_references" ], *inds[ "biocharacteristics" ]  ]

        for mapped in prefixed:
            for pre in kwargs[ "filter_defs" ]:
                try:
                    if re.compile( filter_defs[ pre ][ "pattern" ] ).match( mapped[ "type" ][ "id" ] ):
                        cs[ "info" ][ pre ] = mapped[ "type" ]
                        update_flag = 1
                        break
                except Exception:
                    pass

        if "followup_months" in bios[ "info" ]:
            try:
                if bios[ "info" ][ "followup_months" ]:
                    cs[ "info" ][ "followup_months" ] = float("%.1f" %  bios[ "info" ][ "followup_months" ])
                    update_flag = 1
            except ValueError:
                return False            

        if "death" in bios[ "info" ]:
            if bios[ "info" ][ "death" ]:
                if str(bios[ "info" ][ "death" ]) == "1":
                    cs[ "info" ][ "death" ] = "dead"
                    update_flag = 1
                elif str(bios[ "info" ][ "death" ]) == "0":
                    cs[ "info" ][ "death" ] = "alive"
                    update_flag = 1

        if "age_at_collection" in bios:
            try:
                if bios[ "age_at_collection" ][ "age" ]:    
                    if re.compile( r"P\d" ).match( bios[ "age_at_collection" ][ "age" ] ):
                        cs[ "info" ][ "age_iso" ] = bios[ "age_at_collection" ][ "age" ]
                        cs[ "info" ][ "age_years" ] = _isoage_to_decimal_years(bios[ "age_at_collection" ][ "age" ])
                        update_flag = 1
            except Exception:
                pass


        if update_flag == 1:
                cs_coll.update_one( { "_id" : cs[ "_id" ] }, { "$set": { "info": cs[ "info" ], "updated": datetime.now() } } )

        bar.next()

    bar.finish()
    mongo_client.close()

################################################################################
################################################################################
################################################################################

def _isoage_to_decimal_years(isoage):

    years, months = [ 0, 0 ]
    age_match = re.compile(r"^P(?:(\d+?)Y)?(?:(\d+?))?")
    if age_match.match(isoage):
        y, m = age_match.match(isoage).group(1,2)
        if y:
            years = y * 1
        if m:
            months = m * 1
        dec_age = float(years) + float(months) / 12
        return float("%.1f" % dec_age)

    return

