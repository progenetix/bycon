import csv, datetime, re, requests
from random import sample as randomSamples
from pathlib import Path

from datatable_utils import import_datatable_dict_line
from interval_utils import interval_cnv_arrays
from response_remapping import vrsify_variant
from variant_parsing import variant_create_digest

################################################################################

def read_tsv_to_dictlist(filepath, max_count=0):

    dictlist = []

    with open(filepath, newline='') as csvfile:
    
        data = csv.DictReader(filter(lambda row: row[0]!='#', csvfile), delimiter="\t", quotechar='"')
        fieldnames = list(data.fieldnames)

        for l in data:
            dictlist.append(dict(l))

    if max_count > 0:
        if max_count < len(dictlist):
            dictlist = randomSamples(dictlist, k=max_count)

    return dictlist, fieldnames

################################################################################

def read_www_tsv_to_dictlist(www, max_count=0):

    dictlist = []

    with requests.Session() as s:
        download = s.get(www)
        decoded_content = download.content.decode('utf-8')    
        data = csv.DictReader(filter(lambda row: row[0]!='#', decoded_content.splitlines()), delimiter="\t", quotechar='"')
        fieldnames = list(data.fieldnames)

        for l in data:
            dictlist.append(dict(l))

    if max_count > 0:
        if max_count < len(dictlist):
            dictlist = randomSamples(dictlist, k=max_count)

    return dictlist, fieldnames

################################################################################

def read_pgxseg_file_header(filepath):

    h_lines = []

    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line.startswith("#"):
                h_lines.append(line)

    return h_lines

################################################################################

def pgxseg_return_bycon_bundle(filepath, byc):

    # TODO: bundle as a schema
    bycon_bundle = {
        "variants": [],
        "callsets": [],
        "biosamples": [],
        "individuals": [],
        "ds_id": "File",
        "info": {
            "errors": []
        }
    }

    try:
        Path(filepath).resolve()
        exist = True
    except (OSError, RuntimeError):
        bycon_bundle["info"]["errors"].append(f"The file {filepath} does not exist.")
        return bycon_bundle

    # TODO: "ds_id" from file name

    pgxseg_variants, fieldnames = read_tsv_to_dictlist(filepath)
    if not "biosample_id" in fieldnames:
        bycon_bundle["info"]["errors"].append("¡¡¡ The `biosample_id` parameter is required for variant assignment !!!")
        return bycon_bundle

    #---------------------------- header parsing-------------------------------#

    pgxseg_head = read_pgxseg_file_header(filepath)
    pgx_keyed_bundle = pgxseg_deparse_sample_header(byc, pgxseg_head)

    #--------------------------------------------------------------------------#
    
    inds_ided = pgx_keyed_bundle.get("individuals_by_id", {})
    bios_ided = pgx_keyed_bundle.get("biosamples_by_id", {})
    cs_ided = pgx_keyed_bundle.get("callsets_by_id", {})
    vars_ided = pgx_keyed_bundle.get("variants_by_id", {})

    for c, v in enumerate(pgxseg_variants):
        bs_id = v.get("biosample_id", False)
        if bs_id is False:
            bycon_bundle["info"]["errors"].append("¡¡¡ The `biosample_id` parameter is required for variant assignment !!!")
            return bycon_bundle

        # If the biosample exists in metadata all the other items will exist by id
        if not bs_id in bios_ided:
            cs_id = re.sub(r'^(pgxbs-)?', "pgxcs-", bs_id)
            ind_id = re.sub(r'^(pgxbs-)?', "pgxind-", bs_id)
            cs_ided.update( {cs_id: {"id": cs_id, "biosample_id": bs_id, "individual_id": ind_id } } )
            vars_ided.update( {cs_id: [] } )
            bios_ided.update( {bs_id: {"id": bs_id, "individual_id": ind_id } } )
            inds_ided.update( {ind_id: {"id": ind_id } } )
        else:
            for cs_i, cs_v in cs_ided.items():
                if cs_v.get("biosample_id", "___nothing___") == bs_id:
                    cs_id = cs_i
                    continue
        
        bios = bios_ided.get(bs_id)
        cs = cs_ided.get(cs_id)
        ind_id = bios.get("individual_id", "___nothing___")
        ind = inds_ided.get(ind_id)

        update_v = {
            "individual_id": ind_id,
            "biosample_id": bs_id,
            "callset_id": cs_id,
        }

        update_v = import_datatable_dict_line(byc, update_v, fieldnames, v, "variant")
        vrsify_variant(update_v, byc)
        update_v.update({
            "variant_internal_id": variant_create_digest(update_v, byc),
            "updated": datetime.datetime.now().isoformat()
        })

        vars_ided[cs_id].append(update_v)

    for cs_id, cs_vars in vars_ided.items():
        maps, cs_cnv_stats, cs_chro_stats = interval_cnv_arrays(cs_vars, byc)
        # prjsonnice(cs_chro_stats)
       
        cs_ided[cs_id].update({"cnv_statusmaps": maps})
        cs_ided[cs_id].update({"cnv_stats": cs_cnv_stats})
        cs_ided[cs_id].update({"cnv_chro_stats": cs_chro_stats})
        cs_ided[cs_id].update({ "updated": datetime.datetime.now().isoformat() })

    bycon_bundle["biosamples"] = list(bios_ided.values())
    bycon_bundle["individuals"] = list(inds_ided.values())
    bycon_bundle["callsets"] = list(cs_ided.values())
    bycon_bundle["variants"] = [elem for sublist in (vars_ided.values()) for elem in sublist]

    return bycon_bundle

################################################################################    

def pgxseg_deparse_sample_header(byc, header_lines):

    if type(header_lines) is not list:
        return False

    pgx_keyed_bundle = {
        "variants_by_id": {},
        "callsets_by_id": {},
        "individuals_by_id": {},
        "biosamples_by_id": {},
        "info": {}
    }

    for l in header_lines:
        if not l.startswith("#sample=>"):
            continue       
        l = re.sub("#sample=>", "", l)
        bios_d = {}
        for p_v in l.split(";"):
            k, v = p_v.split("=")
            v = re.sub(r'^[\'\"]', '', v)
            v = re.sub(r'[\'\"]$', '', v)
            # print(f'{k} => {v}')
            bios_d.update({k:v})
        fieldnames = list(bios_d.keys())
        bs_id = bios_d.get("biosample_id")
        if bs_id is None:
            continue

        bios = {"id": bs_id} 
        bios = import_datatable_dict_line(byc, bios, fieldnames, bios_d, "biosample")
        cs_id = bios.get("callset_id", re.sub("pgxbs", "pgxcs", bs_id) )
        ind_id = bios.get("individual_id", re.sub("pgxbs", "pgxind", bs_id) )
        ind = {"id": ind_id} 
        cs = {"id": cs_id, "biosample_id": bs_id, "individual_id": ind_id} 

        bios.update({"individual_id": ind_id})

        pgx_keyed_bundle["callsets_by_id"].update({ cs_id: import_datatable_dict_line(byc, cs, fieldnames, bios_d, "callset") })
        pgx_keyed_bundle["individuals_by_id"].update({ ind_id: import_datatable_dict_line(byc, ind, fieldnames, bios_d, "individual") })
        pgx_keyed_bundle["biosamples_by_id"].update({ bs_id: bios })
        pgx_keyed_bundle["variants_by_id"].update({ cs_id: [] })

    return pgx_keyed_bundle

################################################################################
