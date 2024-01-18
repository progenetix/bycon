import re
from pymongo import MongoClient
from pathlib import Path
from os import environ, pardir, path
import sys

from cgi_parsing import *
from bycon_helpers import hex_2_rgb
from variant_mapping import ByconVariant

################################################################################

def dataset_response_add_handovers(ds_id, byc):

    """podmd
    podmd"""

    b_h_o = [ ]
    if byc["include_handovers"] is not True:
        return b_h_o
    if not ds_id in byc["dataset_definitions"]:
        return b_h_o

    h_o_server = select_this_server(byc)    
    h_o_types = byc["handover_definitions"]["h->o_types"]
    ds_h_o = byc["dataset_definitions"][ ds_id ].get("handoverTypes", h_o_types.keys())

    ds_res_k = list(byc["dataset_results"][ds_id].keys())

    prdbug(f'... pre handover {ds_res_k}', byc.get("debug_mode"))

    for h_o_t, h_o_defs in h_o_types.items():

        h_o_k = h_o_types[ h_o_t ].get("h->o_key", "___none___")
        h_o = byc["dataset_results"][ds_id].get(h_o_k)
        if not h_o:
            continue
        prdbug(f'... checking handover {h_o_t}', byc.get("debug_mode"))

        # testing if this handover is active for the specified dataset      
        if h_o_t not in ds_h_o:
            continue

        target_count =  h_o.get("target_count", 0)
        if target_count < 1:
            continue

        accessid = h_o["id"]
        this_server = h_o_server
        if "remove_subdomain" in h_o_types[ h_o_t ]:
            this_server = re.sub(r'\/\/\w+?\.(\w+?\.\w+?)$', r'//\1', this_server)
        h_o_r = {
            "handover_type": h_o_defs.get("handoverType", {}),
            "info": { "content_id": h_o_t},
            "note": h_o_defs[ "note" ],
            "url": ""
        }

        if "UCSClink" in h_o_t:
            bed_file_name, ucsc_pos = _write_variants_bedfile(h_o, 0, 0, byc)
            h_o_r.update( { "url": _handover_create_ext_url(this_server, h_o_defs, bed_file_name, ucsc_pos, byc ) } )
        else:
            h_o_r.update( { "url": handover_create_url(this_server, h_o_defs, accessid, byc) } )

        # TODO: needs a new schema to accommodate this not as HACK ...
        # the phenopackets URL needs matched variants, which it wouldn't know about ...
        if "phenopackets" in h_o_t:
            if "variants._id" in byc["dataset_results"][ds_id].keys():
                h_o_r["url"] += "&variantsaccessid="+byc["dataset_results"][ds_id][ "variants._id" ][ "id" ]

        e_t = byc["response_entity"].get("response_entity_id", "___none___")
        p_e = h_o_defs.get("paginated_entities", [])

        if e_t in p_e or "all" in p_e:

            h_o_r.update({"pages":[]})
            p_f = 0
            p_t = p_f + byc["pagination"]["limit"]
            p_s = 0

            while p_f < target_count + 1:
                if target_count < p_t:
                    p_t = target_count
                l = "{}-{}".format(p_f + 1, p_t)
                # no re-pagination of the results retrieved from the paginated query
                # TODO: the bedfile part is wrong, since it paginates by the number of variants which
                # may be incorrect if biosamples ... were called. have to change...
                if "bedfile" in h_o_t:
                    bed_file_name, ucsc_pos = _write_variants_bedfile(h_o, p_f, p_t, byc)
                    u =  _handover_create_ext_url(this_server, h_o_defs, bed_file_name, ucsc_pos, byc )
                else:
                    u = h_o_r["url"] + "&paginateResults=false&skip={}&limit={}".format(p_s, byc["pagination"]["limit"])
                h_o_r["pages"].append( { "handover_type": {"id": h_o_defs["handoverType"][ "id" ], "label": l }, "url": u } )
                p_s += 1
                p_f += byc["pagination"]["limit"]
                p_t = p_f + byc["pagination"]["limit"]

            h_o_r["url"] += "&skip={}&limit={}".format(byc["pagination"]["skip"], byc["pagination"]["limit"])
        if "url" in h_o_r:
            b_h_o.append( h_o_r )

    return b_h_o


################################################################################

def dataset_results_save_handovers(ds_id, byc):

    ho_client = MongoClient(host=environ.get("BYCON_MONGO_HOST", "localhost"))
    ho_db = ho_client[ byc["housekeeping_db"] ]
    ho_coll = ho_db[ byc[ "handover_coll" ] ]

    for h_o_k in byc["dataset_results"][ds_id].keys():
        
        h_o = byc["dataset_results"][ds_id][ h_o_k ]
        h_o_size = sys.getsizeof(h_o["target_values"])

        # print("Storage size for {}: {}Mb".format(h_o_k, h_o_size / 1000000))
        if h_o_size < 15000000:
            ho_coll.update_one( { "id": h_o["id"] }, { '$set': h_o }, upsert=True )

    ho_client.close()

    return True


################################################################################

def handover_create_url(h_o_server, h_o_defs, accessid, byc):

    if "script_path_web" in h_o_defs:
        server = h_o_server
        if "http" in h_o_defs["script_path_web"]:
            server = ""
        url = "{}{}?accessid={}".format(server, h_o_defs["script_path_web"], accessid)
        for p in ["method", "output", "plotType", "requestedSchema"]:
            if p in h_o_defs:
                url += "&{}={}".format(p, h_o_defs[p])
        url += h_o_defs.get("url_opts", "")
        # p_t = h_o_defs.get("plotType")
        # if p_t:
        #     url += _handover_add_stringified_plot_parameters(byc)

        return url

    return ""


################################################################################

def _handover_create_ext_url(h_o_server, h_o_defs, bed_file_name, ucsc_pos, byc):

    local_paths = byc.get("local_paths")
    if not local_paths:
        return False

    if "ext_url" in h_o_defs:
        if "bedfile" in h_o_defs["handoverType"]["id"]:
            return("{}&position={}&hgt.customText={}{}/{}".format(h_o_defs["ext_url"], ucsc_pos, h_o_server, local_paths.get("server_tmp_dir_web", "/tmp"), bed_file_name))

    return False


################################################################################

def _write_variants_bedfile(h_o, p_f, p_t, byc):

    """podmd
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

    local_paths = byc.get("local_paths")
    if not local_paths:
        return False
    tmp_path = Path( path.join( *local_paths[ "server_tmp_dir_loc" ]) )
    if not tmp_path.is_dir():
        return False

    v_ret = 0
    v_max = 1000

    if len( h_o["target_values"] ) < 1:
        return()
    if not h_o["target_collection"] == "variants":
         return()
       
    ds_id = h_o["source_db"]
    accessid = h_o["id"]
    l = ""
    if p_t > 0:
        l = "_{}-{}".format(p_f + 1, p_t)
    else:
        p_t = v_max # only for the non-paginated ...

    bed_file_name = f'{accessid}{l}.bed'
    bed_file = Path( path.join( tmp_path, bed_file_name ) )

    vs = { "DUP": [ ], "DEL": [ ], "LOH": [ ], "SNV": [ ]}

    data_client = MongoClient(host=environ.get("BYCON_MONGO_HOST", "localhost"))
    data_db = data_client[ ds_id ]
    data_coll = data_db[ h_o["target_collection"] ]

    for v in data_coll.find( { h_o["target_key"]: { '$in': h_o["target_values"] } }).limit(p_t):

        v_ret += 1

        if p_t > 0:
            if v_ret > p_t:
                continue
            if v_ret <= p_f:
                continue
        
        # TODO: Just make this from the standard variant format
        pv = ByconVariant(byc).byconVariant(v)

        if "DUP" in pv["variant_type"]:
            vs["DUP"].append(pv)
        elif "DEL" in pv["variant_type"]:
            vs["DEL"].append(pv)
        elif "LOH" in pv["variant_type"]:
            vs["LOH"].append(pv)
        elif "SNV" in pv["variant_type"]:
            vs["SNV"].append(pv)
        else:
            continue

    b_f = open( bed_file, 'w' )
    pos = set()

    ucsc_chr = ""

    colors = {
        "plot_dup_color": "#FFC633",
        "plot_amp_color": "#FF6600",
        "plot_del_color": "#33A0FF",
        "plot_homodel_color": "#0033CC"
    }

    for vt in vs.keys():
        if len( vs[vt] ) > 0:
            try:
                vs[vt] = sorted(vs[vt], key=lambda k: k['variant_length'], reverse=True)
            except:
                pass
            col_key = "plot_{}_color".format(vt.lower())
            col_hex = colors.get(col_key, "#666666")
            col_rgb = hex_2_rgb(col_hex)
            # col_rgb = [127, 127, 127]
            b_f.write("track name={} visibility=squish description=\"{} variants matching the query with {} overall returned\" color={},{},{}\n".format(vt, vt, v_ret, col_rgb[0], col_rgb[1], col_rgb[2] ) )
            b_f.write("#chrom\tchromStart\tchromEnd\tbiosampleId\n")
            for v in vs[vt]:
                ucsc_chr = "chr"+v["reference_name"]
                ucsc_min = int( v["start"] + 1 )
                ucsc_max = int( v["end"] )
                l = "{}\t{}\t{}\t{}\n".format( ucsc_chr, ucsc_min, ucsc_max, v["biosample_id"] )
                pos.add(ucsc_min)
                pos.add(ucsc_max)
                b_f.write( l )
 
    b_f.close()
    ucsc_range = sorted(pos)
    ucsc_pos = "{}:{}-{}".format(ucsc_chr, ucsc_range[0], ucsc_range[-1])

    return [bed_file_name, ucsc_pos]

################################################################################

