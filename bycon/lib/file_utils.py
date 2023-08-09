import csv
import datetime
import re
import requests
from pathlib import Path
from os import path
from copy import deepcopy
from random import sample as random_samples

from cgi_parsing import prjsonnice
from datatable_utils import import_datatable_dict_line
from interval_utils import interval_cnv_arrays, interval_counts_from_callsets
from variant_mapping import ByconVariant


################################################################################

def read_tsv_to_dictlist(filepath, max_count=0):

    dictlist = []

    with open(filepath, newline='') as csvfile:
    
        data = csv.DictReader(filter(lambda row: row[0]!='#', csvfile), delimiter="\t", quotechar='"')
        fieldnames = list(data.fieldnames)

        for l in data:
            dictlist.append(dict(l))
            # prjsonnice(dict(l))

    if 0 < max_count < len(dictlist):
        dictlist = random_samples(dictlist, k=max_count)

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

    if 0 < max_count < len(dictlist):
        dictlist = random_samples(dictlist, k=max_count)

    return dictlist, fieldnames

################################################################################

def callset_guess_probefile_path(callset, byc):

    local_paths = byc.get("local_paths")
    if not local_paths:
        return False

    if not "server_callsets_dir_loc" in local_paths:
        return False

    if not "analysis_info" in callset:
        return False

    d = Path( path.join( *byc["local_paths"]["server_callsets_dir_loc"]))
    n = byc["config"].get("callset_probefile_name", "___none___")

    if not d.is_dir():
        return False

    # TODO: not only geo cleaning?
    s_id = callset["analysis_info"].get("series_id", "___none___").replace("geo:", "")
    e_id = callset["analysis_info"].get("experiment_id", "___none___").replace("geo:", "")

    p_f = Path( path.join( d, s_id, e_id, n ) )

    if not p_f.is_file():
        return False

    return p_f


################################################################################
################################################################################
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

    def __init__(self, byc):

        self.byc = byc
        self.errors = []
        self.filepath = None
        self.header = []
        self.data = []
        self.fieldnames = []
        self.callsetVariantsBundles = []
        self.intervalFrequenciesBundles = []

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

    def read_pgx_file(self, filepath):

        self.filepath = filepath

        h_lines = []

        with open(self.filepath) as f:
            for line in f:
                line = line.strip()
                if line.startswith("#"):
                    h_lines.append(line)

        d_lines, fieldnames = read_tsv_to_dictlist(self.filepath, max_count=0)

        self.header = h_lines
        self.data = d_lines
        self.fieldnames = fieldnames

        return self
        

    #--------------------------------------------------------------------------#

    def read_probedata_file(self, filepath):

        self.filepath = filepath
        self.probedata = []

        p_lines, fieldnames = read_tsv_to_dictlist(self.filepath, max_count=0)

        p_o = {
            "probe_id": False,
            "reference_name": False,
            "start": False,
            "value": False
        }

        p_f_d = {
            "probe_id": {"type": "string", "key": fieldnames[0]},
            "reference_name": {"type": "string", "key": fieldnames[1]},
            "start": {"type": "integer", "key": fieldnames[2]},
            "value": {"type": "number", "key": fieldnames[3]}
        }

        for l in p_lines:
            p = deepcopy(p_o)
            for pk, pv in p_f_d.items():
                l_k = pv["key"]
                p.update({ pk: l.get(l_k) })
                if "int" in pv["type"]:
                    p.update({ pk: int(p[pk]) })
                elif "num" in pv["type"]:
                    p.update({ pk: float(p[pk]) })
            self.probedata.append(p)

        return self.probedata

    #--------------------------------------------------------------------------#

    def pgxseg_to_keyed_bundle(self, filepath):
        self.read_pgx_file(filepath)

        if not "biosample_id" in self.fieldnames:
            self.errors.append("¡¡¡ The `biosample_id` parameter is required for variant assignment !!!")
            return

        self.__deparse_pgxseg_samples_header()
        self.__keyed_bundle_add_variants()

        return self.keyedBundle

    #--------------------------------------------------------------------------#

    def pgxseg_to_bundle(self, filepath):

        self.pgxseg_to_keyed_bundle(filepath)
        self.__flatten_keyed_bundle()

        return self.bundle


    #--------------------------------------------------------------------------#

    def callsets_variants_bundles(self):

        # TODO: This is similar to a keyed bundle component ...

        bb = self.bundle

        c_p_l = []
        for p_o in bb.get("callsets", []):
            cs_id = p_o.get("id")
            p_o.update({
                "ds_id": bb.get("ds_id", ""),
                "variants":[]
            })
            for v in bb["variants"]:
                if v.get("callset_id", "") == cs_id:
                    p_o["variants"].append(ByconVariant(self.byc).byconVariant(v))

            c_p_l.append(p_o)
            
        self.callsetVariantsBundles = c_p_l

        return self.callsetVariantsBundles

    #--------------------------------------------------------------------------#

    def callsets_frequencies_bundles(self):
            
        self.intervalFrequenciesBundles.append(self.__callsetBundleCreateIset("import"))

        return self.intervalFrequenciesBundles


    #--------------------------------------------------------------------------#
    #----------------------------- private ------------------------------------#
    #--------------------------------------------------------------------------#

    def __deparse_pgxseg_samples_header(self):

        b_k_b = self.keyedBundle
        h_l = self.header

        for l in h_l:
            if not l.startswith("#sample=>"):
                continue       
            l = re.sub("#sample=>", "", l)
            bios_d = {}
            for p_v in l.split(";"):
                k, v = p_v.split("=")
                v = re.sub(r'^[\'\"]', '', v)
                v = re.sub(r'[\'\"]$', '', v)
                bios_d.update({k:v})
            fieldnames = list(bios_d.keys())
            bs_id = bios_d.get("biosample_id")
            if bs_id is None:
                continue

            bios = {"id": bs_id} 
            bios = import_datatable_dict_line(self.byc, bios, fieldnames, bios_d, "biosample")
            cs_id = bios.get("callset_id", re.sub("pgxbs", "pgxcs", bs_id) )
            ind_id = bios.get("individual_id", re.sub("pgxbs", "pgxind", bs_id) )
            ind = {"id": ind_id} 
            cs = {"id": cs_id, "biosample_id": bs_id, "individual_id": ind_id} 

            bios.update({"individual_id": ind_id})

            # b_k_b["callsets_by_id"].update({ cs_id: import_datatable_dict_line(self.byc, cs, fieldnames, bios_d, "analysis") })
            # b_k_b["individuals_by_id"].update({ ind_id: import_datatable_dict_line(self.byc, ind, fieldnames, bios_d, "individual") })
            b_k_b["callsets_by_id"].update({ cs_id: cs })
            b_k_b["individuals_by_id"].update({ ind_id: ind })
            b_k_b["biosamples_by_id"].update({ bs_id: bios })
            b_k_b["variants_by_callset_id"].update({ cs_id: [] })

        self.keyedBundle = b_k_b


    #--------------------------------------------------------------------------#

    def __keyed_bundle_add_variants(self):

        fieldnames = self.fieldnames
        varlines = self.data

        b_k_b = self.keyedBundle

        inds_ided = b_k_b.get("individuals_by_id", {})
        bios_ided = b_k_b.get("biosamples_by_id", {})
        cs_ided = b_k_b.get("callsets_by_id", {})

        vars_ided = b_k_b.get("variants_by_callset_id", {})

        for v in varlines:

            bs_id = v.get("biosample_id", "___none___")

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

            update_v = import_datatable_dict_line(self.byc, update_v, fieldnames, v, "genomicVariant")
            update_v = ByconVariant(self.byc).pgxVariant(update_v)
            update_v.update({
                "updated": datetime.datetime.now().isoformat()
            })

            vars_ided[cs_id].append(update_v)

        for cs_id, cs_vars in vars_ided.items():
            maps, cs_cnv_stats, cs_chro_stats = interval_cnv_arrays(cs_vars, self.byc)           
            cs_ided[cs_id].update({"cnv_statusmaps": maps})
            cs_ided[cs_id].update({"cnv_stats": cs_cnv_stats})
            cs_ided[cs_id].update({"cnv_chro_stats": cs_chro_stats})
            cs_ided[cs_id].update({"updated": datetime.datetime.now().isoformat()})

        self.keyedBundle.update({
            "individuals_by_id": inds_ided,
            "biosamples_by_id": bios_ided,
            "callsets_by_id": cs_ided,
            "variants_by_callset_id": vars_ided
        })

    #--------------------------------------------------------------------------#

    def __flatten_keyed_bundle(self):

        b_k_b = self.keyedBundle

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

    #--------------------------------------------------------------------------#

    def __callsetBundleCreateIset(self, label=""):

        intervals, cnv_cs_count = interval_counts_from_callsets(self.bundle["callsets"], self.byc)

        ds_id = self.bundle.get("ds_id", "")
        iset = {
            "dataset_id": ds_id,
            "group_id": ds_id,
            "label": label,
            "sample_count": cnv_cs_count,
            "interval_frequencies": []
        }

        for intv_i, intv in enumerate(intervals):
            iset["interval_frequencies"].append(intv.copy())

        return iset

################################################################################
