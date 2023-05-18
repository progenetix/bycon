import csv, datetime, re, requests, typing
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

class ByconBundler:

    """
    # The `ByconBundler` class

    This class bundles documents from the main entities which have a complete
    intersection - e.g. for a set of variants their callsets, biosamples and
    individuals. The bundling does _not_ have to be complete; e.g. bundles may
    be based on only some matched variants (not all variants of the referenced
    callsets); and bundles may have empty lists for some entities.
    """

    def __init__(self, byc, **kwargs):

        self.byc = byc
        self.filepath = kwargs.get("filepath")
        self.bundle = {
            "variants": [],
            "callsets": [],
            "biosamples": [],
            "individuals": [],
            "ds_id": None,
            "info": {
                "errors": []
            }
        }

        self.keyedBundle = {
            "variants_by_callset_id": {},
            "callsets_by_id": {},
            "individuals_by_id": {},
            "biosamples_by_id": {},
            "ds_id": None,
            "info": {
                "errors": []
            }
        }

    #--------------------------------------------------------------------------#
    #----------------------------- public -------------------------------------#
    #--------------------------------------------------------------------------#

    def emptyBundle(self):
        return self.bundle

    #--------------------------------------------------------------------------#

    def emptyKeyedBundle(self):
        return self.keyedBundle

    #--------------------------------------------------------------------------#

    def flattenedBundle(self, b_k_b={}):
        self.__flatten_keyed_bundle(b_k_b)
        return self.bundle

    #--------------------------------------------------------------------------#

    def readPgxseg(self, filename):

        self.pgxseg = {}

        return self.pgxseg

    #--------------------------------------------------------------------------#

    def pgxseg2bundle(self, filename):

        self.readPgxseg(filename)

        return self.pgxseg

    #--------------------------------------------------------------------------#
    #----------------------------- private ------------------------------------#
    #--------------------------------------------------------------------------#

    def __pgxseg_2_bundle(self):

        # TBD

        return

    #--------------------------------------------------------------------------#


    def __flatten_keyed_bundle(self, b_k_b):

        bios_k = b_k_b.get("biosamples_by_id", {})
        ind_k = b_k_b.get("individuals_by_id", {})
        cs_k = b_k_b.get("callsets_by_id", {})
        v_cs_k = b_k_b.get("variants_by_callset_id", {})

        self.bundle.update({
            "biosamples": list( bios_k.values() ),
            "individuals": list( ind_k.values() ),
            "callsets": list( cs_k.values() ),
            "variants": [elem for sublist in ( v_cs_k.values() ) for elem in sublist]
        })

################################################################################

def pgxseg_return_bycon_bundle(filepath, byc):

    # TODO: bundle as a schema
    bycon_bundle = ByconBundler(byc).emptyBundle()

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
    b_k_b = pgxseg_deparse_sample_header(byc, pgxseg_head)

    #--------------------------------------------------------------------------#
    
    inds_ided = b_k_b.get("individuals_by_id", {})
    bios_ided = b_k_b.get("biosamples_by_id", {})
    cs_ided = b_k_b.get("callsets_by_id", {})
    vars_ided = b_k_b.get("variants_by_callset_id", {})

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

    b_k_b.update({
        "individuals_by_id": inds_ided,
        "biosamples_by_id": bios_ided,
        "callsets_by_id": cs_ided,
        "variants_by_callset_id": vars_ided
    })

    flattened_bundle = ByconBundler(byc).flattenedBundle(b_k_b)

    for k, v in flattened_bundle.items():
        bycon_bundle.update({ k: v })

    return bycon_bundle

################################################################################    

def pgxseg_deparse_sample_header(byc, header_lines):

    if type(header_lines) is not list:
        return False

    b_k_b = ByconBundler(byc).emptyKeyedBundle()

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

        b_k_b["callsets_by_id"].update({ cs_id: import_datatable_dict_line(byc, cs, fieldnames, bios_d, "analysis") })
        b_k_b["individuals_by_id"].update({ ind_id: import_datatable_dict_line(byc, ind, fieldnames, bios_d, "individual") })
        b_k_b["biosamples_by_id"].update({ bs_id: bios })
        b_k_b["variants_by_callset_id"].update({ cs_id: [] })

    return b_k_b

################################################################################
