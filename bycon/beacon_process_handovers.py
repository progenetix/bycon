import re, yaml
from pymongo import MongoClient
from os import path as path
from os import environ

from .cgi_utils import *

################################################################################

def dataset_response_add_handovers(ds_id, **byc):

    """podmd
    #### Beacon "Handovers"

    Beacon `handover` objects represent an efficient and - if used properly -
    privacy protecting mechanism to enable data delivery, in conjunction with
    Beacon queries.

    The advantages of using the "handover" mechanism lie especially in:

    * the separation of the standard Beacon variant query and response with the privvacy-protecting
    response, limited to yes/no/count, from meta-information about individuals and
    biosamples
    * the power to link to any type of data delivery protocol for "documents"
    (i.e. database records) related to the Beacon query matches

    Handled in a controled/protected environment one could in pprinciple use e.g.
    the `handover` protocol to access the electronic health records (EHR) of patients
    for which a specific genomic variantr query resulte din a match, to follow up 
    on thiose patients' history & progress, or to initiate interventions based on
    accuing evidence related to the matched variant(s).

    While the `handover` mechanisms is powerful through its flexibility, an obvious
    disadvantage lies in the lack of control about the implemented mechanisms. A
    good siolution here would be to provide some prototype designs, e.g. "Phenopackets"
    formatted delivery of "bio" data.s

    podmd"""

    h_o_server = _handover_select_server(**byc) 
    b_h_o = [ ]

    if not ds_id in byc["datasets_info"]:
        return b_h_o

    ds_h_o =  byc["datasets_info"][ ds_id ]["handoverTypes"]
    h_o_types = byc["h->o"]["h->o_types"]

    for h_o_t in h_o_types.keys():

        # testing if this handover is active fo the specified dataset
        h_o_defs = h_o_types[ h_o_t ]

        if not h_o_t in ds_h_o:
            continue

        for h_o_key in byc[ "query_results" ].keys():
            h_o = byc[ "query_results" ][ h_o_key ]
            if h_o["target_count"] < 1:
                continue
            accessid = h_o["id"]
            if h_o_key == h_o_types[ h_o_t ][ "h->o_key" ]:
                this_server = h_o_server
                if "remove_subdomain" in h_o_types[ h_o_t ]:
                    this_server = re.sub(r'\/\/\w+?\.(\w+?\.\w+?)$', r'//\1', this_server)
                h_o_r = {
                    "handoverType": {
                        "id": h_o_defs[ "id" ],
                        "label": h_o_defs[ "label" ],
                    },
                    "description": h_o_defs[ "description" ],
                }

                if "bedfile" in h_o_defs[ "id" ]:
                    ucsc_pos = _write_variants_bedfile(h_o, **byc)
                    h_o_r.update( { "url": _handover_create_ext_url(this_server, h_o_defs, h_o_t, accessid, ucsc_pos ) } )
                else:
                    h_o_r.update( { "url": _handover_create_url(this_server, h_o_defs, h_o_t, accessid) } )

                # TODO: needs a new schema to accommodate this not as HACK ...
                # the phenopackets URL needs matched variants, which it wouldn't know about ...
                if "phenopackets" in h_o_t:
                    if "vs._id" in byc[ "query_results" ].keys():
                        h_o_r["url"] += "&variantsaccessid="+byc[ "query_results" ][ "vs._id" ][ "id" ]

                b_h_o.append( h_o_r )

    return b_h_o

################################################################################

def query_results_save_handovers( **byc ):

    ho_client = MongoClient()
    ho_db = ho_client[ byc["config"]["info_db"] ]
    ho_coll = ho_db[ byc["config"][ "handover_coll" ] ]

    for h_o_k in byc[ "query_results" ].keys():
        h_o = byc[ "query_results" ][ h_o_k ]
        ho_coll.update_one( { "id": h_o["id"] }, { '$set': h_o }, upsert=True )

    ho_client.close()

    return True

################################################################################

def retrieve_handover( accessid, **byc ):

    mongo_client = MongoClient()
    ho_d = byc["config"]["info_db"]
    ho_c = byc["config"][ "handover_coll" ]
    ho_coll = mongo_client[ ho_d ][ ho_c ]

    h_o = { }
    error = False

    try:
        h_o =  ho_coll.find_one( { "id": accessid } )
    except:
        pass

    mongo_client.close( )

    return h_o, error

###############################################################################

def handover_return_data( h_o, error ):

    mongo_client = MongoClient()
    data = [ ]

    if not error:
        data_coll = mongo_client[ h_o["source_db"] ][ h_o[ "target_collection" ] ]
        query = { h_o["target_key"]: { '$in': h_o["target_values"] } }
        for c in data_coll.find( query, {'_id': False } ):
            data.append(c)
    else:
        pass
    # TODO: error messaging

    mongo_client.close( )

    return data, error

################################################################################

def _handover_select_server( **byc ):

    s_uri = str(environ.get('SCRIPT_URI'))
    if "https:" in s_uri:
        return "https://"+str(environ.get('HTTP_HOST'))
    else:
        return "http://"+str(environ.get('HTTP_HOST'))

################################################################################

def _handover_create_url(h_o_server, h_o_defs, h_o_t, accessid):

    if "script_path_web" in h_o_defs:
        server = h_o_server
        if "http" in h_o_defs["script_path_web"]:
            server = ""
        # TODO: hacking deliveries to force simple list for interface => next
        opts = ""
        if "deliveries" in h_o_defs["script_path_web"]:
            opts = "&responseFormat=simplelist"
        return("{}{}?do={}&accessid={}{}".format(server, h_o_defs["script_path_web"], h_o_t, accessid, opts))

    return ""

################################################################################

def _handover_create_ext_url(h_o_server, h_o_defs, h_o_t, accessid, ucsc_pos):

    if "ext_url" in h_o_defs:
        if "bedfile" in h_o_defs["id"]:
            return("{}&position={}&hgt.customText={}/tmp/{}.bed".format(h_o_defs["ext_url"], ucsc_pos, h_o_server, accessid))

    return False

################################################################################

def _write_variants_bedfile(h_o, **byc):

    """podmd
    #### `BeaconPlus::DataExporter::write_variants_bedfile`

    ##### Accepts

    * a Bycon `byc` object
    * a Bycon `h_o` handover object with its `target_values` representing `_id` 
    objects of a `variants` collection
        
    The function creates a basic BED file and returns its local path. A standard 
    use would be to create a link to this file and submit it as `hgt.customText` 
    parameter to the UCSC browser.

    ##### TODO

    * The creation of the different variant types is still rudimentary and has to be 
    expanded in lockstep with improving Beacon documentation and examples. The 
    definition of the types and their match patterns should also be moved to a 
    +separate configuration entry and subroutine.
    * evaluate to use "bedDetails" format

    podmd"""
 
    if len( h_o["target_values"] ) < 1:
        return()
    if not h_o["target_collection"] == "variants":
         return()
       
    ds_id = h_o["source_db"]
    accessid = h_o["id"]
    bed_file = path.join( byc["config"][ "paths" ][ "out" ], h_o["id"]+'.bed' )

    vs = { "DUP": [ ], "DEL": [ ], "SNV": [ ]}

    data_client = MongoClient( )
    data_db = data_client[ ds_id ]
    data_coll = data_db[ h_o["target_collection"] ]

    for v in data_coll.find( { h_o["target_key"]: { '$in': h_o["target_values"] } }):

        if "variant_type" in v:
            if v["variant_type"] == "DUP":
                vs["DUP"].append(v)
            elif  v["variant_type"] == "DEL":
                vs["DEL"].append(v)
        elif "reference_bases" in v:
            vs["SNV"].append(v)

    b_f = open( bed_file, 'w' )

    pos = set()

    ucsc_chr = ""

    for vt in vs.keys():
        if len( vs[vt] ) > 0:
            col_key = "color_var_"+vt.lower()+"_rgb"
            b_f.write("track name={} visibility=squish description=\"{} variants matching the query\" color={}\n".format(vt, vt, byc["config"]["plot_pars"][col_key]) )
            b_f.write("#chrom\tchromStart\tchromEnd\tbiosampleId\n")
            for v in vs[vt]:
                ucsc_chr = "chr"+v["reference_name"]
                ucsc_min = int( v["start_min"] + 1 )
                ucsc_max = int( v["end_max"] )
                l = "{}\t{}\t{}\t{}\n".format( ucsc_chr, ucsc_min, ucsc_max, v["biosample_id"]+"___"+v["digest"] )
                pos.add(ucsc_min)
                pos.add(ucsc_max)
                b_f.write( l )
 
    b_f.close()
    ucsc_range = sorted(pos)
    ucsc_pos = "{}:{}-{}".format(ucsc_chr, ucsc_range[0], ucsc_range[-1])

    return ucsc_pos

