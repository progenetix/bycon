import csv, re, sys

from datetime import datetime

from os import environ, path
from pymongo import MongoClient
from copy import deepcopy

from bycon import (
    BYC,
    BYC_PARS,
    DB_MONGOHOST,
    ByconVariant,
    GenomeBins,
    return_paginated_list,
    prdbug
)

services_lib_path = path.join( path.dirname( path.abspath(__file__) ) )
sys.path.append( services_lib_path )
from datatable_utils import import_datatable_dict_line
from file_utils import *
from service_response_generation import CollationQuery

################################################################################
################################################################################
################################################################################

class ByconBundler:
    """
    # The `ByconBundler` class

    This class bundles documents from the main entities which have a complete
    intersection - e.g. for a set of variants their analyses, biosamples and
    individuals. The bundling does _not_ have to be complete; e.g. bundles may
    be based on only some matched variants (not all variants of the referenced
    analyses); and bundles may have empty lists for some entities.
    """

    def __init__(self):
        self.errors = []
        self.filepath = None
        self.datset_ids = BYC.get("BYC_DATASET_IDS", [])
        self.datasets_results = None
        self.collation_types = BYC_PARS.get("collation_types", [])
        self.min_number = BYC_PARS.get("min_number", 0)
        self.header = []
        self.data = []
        self.fieldnames = []
        self.analysisVariantsBundles = []
        self.intervalFrequenciesBundles = []
        self.limit = BYC_PARS.get("limit", 0)
        self.skip = BYC_PARS.get("skip", 0)

        self.bundle = {
            "variants": [],
            "analyses": [],
            "biosamples": [],
            "individuals": [],
            "info": {
                "errors": []
            }
        }

        self.keyedBundle = {
            "variants_by_analysis_id": {},
            "analyses_by_id": {},
            "individuals_by_id": {},
            "biosamples_by_id": {},
            "info": {
                "errors": []
            }
        }

        self.plotDataBundle = {
            "interval_frequencies_bundles": [],
            "analyses_variants_bundles": []
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
        prdbug(f'... read_pgx_file with {len(h_lines)} metadata lines')

        d_lines, fieldnames = ByconTSVreader().file_to_dictlist(self.filepath, max_count=0)
        self.header = h_lines
        self.data = d_lines
        self.fieldnames = fieldnames

        return self
        

    #--------------------------------------------------------------------------#

    def read_probedata_file(self, filepath):
        self.filepath = filepath
        self.probedata = []

        p_lines, fieldnames = ByconTSVreader().file_to_dictlist(self.filepath, max_count=0)

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
        self.__keyed_bundle_add_variants_from_lines()

        return self.keyedBundle


    #--------------------------------------------------------------------------#

    def pgxseg_to_plotbundle(self, filepath):
        self.pgxseg_to_keyed_bundle(filepath)
        self.__flatten_keyed_bundle()

        afb = self.analyses_frequencies_bundles()
        avb = self.analyses_variants_bundles()

        return {
            "interval_frequencies_bundles": afb,
            "analyses_variants_bundles": avb
        }


    #--------------------------------------------------------------------------#

    def analyses_variants_bundles(self):
        # TODO: This is similar to a keyed bundle component ...
        bb = self.bundle
        c_p_l = []
        for p_o in bb.get("analyses", []):
            cs_id = p_o.get("id")
            p_o.update({
                "variants": list(filter(lambda v: v.get("analysis_id", "___none___") == cs_id, bb["variants"]))
            })
            c_p_l.append(p_o)          
        self.analysisVariantsBundles = c_p_l
        return self.analysisVariantsBundles


    #--------------------------------------------------------------------------#

    def resultsets_analysis_bundles(self, datasets_results={}):
        self.datasets_results = datasets_results
        self.__analyses_bundle_from_result_set()
        self.__analyses_add_database_variants()
        return { "analyses_variants_bundles": self.analysisVariantsBundles }


    #--------------------------------------------------------------------------#

    def resultsets_frequencies_bundles(self, datasets_results={}):
        self.datasets_results = datasets_results
        self.__analyses_bundle_from_result_set()
        self.__analysisBundleCreateIsets()
        return {"interval_frequencies_bundles": self.intervalFrequenciesBundles}


    #--------------------------------------------------------------------------#

    def analyses_frequencies_bundles(self):
        self.__fileAnalysisBundleCreateIsets()
        return self.intervalFrequenciesBundles


    #--------------------------------------------------------------------------#

    def collationsPlotbundles(self):       
        if len(self.datset_ids) < 1:
            BYC["ERRORS"].append("¡¡¡ No `datasetdIds` parameter !!!")
            return
        self.__isetBundlesFromCollationParameters()
        self.plotDataBundle.update({ "interval_frequencies_bundles": self.intervalFrequenciesBundles })
        return self.plotDataBundle


    #--------------------------------------------------------------------------#
    #----------------------------- private ------------------------------------#
    #--------------------------------------------------------------------------#

    def __deparse_pgxseg_samples_header(self):
        dbm = f'... __deparse_pgxseg_samples_header'
        b_k_b = self.keyedBundle
        h_l = self.header

        for l in h_l:
            if not l.startswith("#sample=>"):
                continue       
            l = re.sub("#sample=>", "", l)
            bios_d = {}
            for p_v in l.split(";"):
                if len(p_v.split("=")) < 2:
                    continue
                k, v = p_v.split("=")
                v = re.sub(r'^[\'\"]', '', v)
                v = re.sub(r'[\'\"]$', '', v)
                bios_d.update({k:v})
            fieldnames = list(bios_d.keys())
            if not (bs_id := bios_d.get("biosample_id")):
                continue

            bios = {"id": bs_id} 
            bios = import_datatable_dict_line(bios, fieldnames, bios_d, "biosample")
            cs_id = bios.get("analysis_id", re.sub("pgxbs", "pgxcs", bs_id) )
            ind_id = bios.get("individual_id", re.sub("pgxbs", "pgxind", bs_id) )
            ind = {"id": ind_id} 
            cs = {"id": cs_id, "biosample_id": bs_id, "individual_id": ind_id}

            bios.update({"individual_id": ind_id})

            b_k_b["analyses_by_id"].update({ cs_id: cs })
            b_k_b["individuals_by_id"].update({ ind_id: ind })
            b_k_b["biosamples_by_id"].update({ bs_id: bios })
            b_k_b["variants_by_analysis_id"].update({ cs_id: [] })

        self.keyedBundle = b_k_b


    #--------------------------------------------------------------------------#

    def __analyses_bundle_from_result_set(self):
        # TODO: doesn't really work for biosamples until we have status maps etc.
        bundle_type = "analyses"
        for ds_id, ds_res in self.datasets_results.items():
            prdbug(f'... __analyses_bundle_from_result_set {ds_id} => {ds_res.keys()}')
            res_k = f'{bundle_type}.id'
            if not ds_res:
                continue
            if not res_k in ds_res:
                continue

            mongo_client = MongoClient(host=DB_MONGOHOST)
            sample_coll = mongo_client[ds_id][bundle_type]
            s_r = ds_res[res_k]
            s_ids = s_r["target_values"]
            r_no = len(s_ids)
            prdbug(f'...... __analyses_bundle_from_result_set limit: {self.limit}')
            s_ids = return_paginated_list(s_ids, self.skip, self.limit)
            prdbug(f'...... __analyses_bundle_from_result_set after: {len(s_ids)}')
            for s_id in s_ids:
                s = sample_coll.find_one({"id": s_id })

                cnv_chro_stats = s.get("cnv_chro_stats", False)
                cnv_statusmaps = s.get("cnv_statusmaps", False)

                if cnv_chro_stats is False or cnv_statusmaps is False:
                    continue

                p_o = {
                    "dataset_id": ds_id,
                    "analysis_id": s.get("id", "NA"),
                    "biosample_id": s.get("biosample_id", "NA"),
                    "label": s.get("label", s.get("biosample_id", "")),
                    "cnv_chro_stats": s.get("cnv_chro_stats"),
                    "cnv_statusmaps": s.get("cnv_statusmaps"),
                    # "probefile": analysis_guess_probefile_path(s),
                    "variants": []
                }

                # TODO: add optional probe read in
                self.bundle[bundle_type].append(p_o)
            prdbug(f'...... __analyses_bundle_from_result_set number: {len(self.bundle[bundle_type])}')

        return


    #--------------------------------------------------------------------------#

    def __analyses_add_database_variants(self):
        bb = self.bundle
        c_p_l = []

        mongo_client = MongoClient(host=DB_MONGOHOST)
        for p_o in bb.get("analyses", []):
            ds_id = p_o.get("dataset_id", "___none___")
            var_coll = mongo_client[ds_id]["variants"]
            cs_id = p_o.get("analysis_id", "___none___")
            v_q = {"analysis_id": cs_id}
            p_o.update({"variants": list(var_coll.find(v_q))})
            c_p_l.append(p_o)

        self.analysisVariantsBundles = c_p_l
        return


    #--------------------------------------------------------------------------#

    def __keyed_bundle_add_variants_from_lines(self):
        fieldnames = self.fieldnames
        varlines = self.data

        b_k_b = self.keyedBundle
        inds_ided = b_k_b.get("individuals_by_id", {})
        bios_ided = b_k_b.get("biosamples_by_id", {})
        cs_ided = b_k_b.get("analyses_by_id", {})
        vars_ided = b_k_b.get("variants_by_analysis_id", {})

        GB = GenomeBins()

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
            ind_id = bios.get("individual_id", "___none___")
            ind = inds_ided.get(ind_id)

            update_v = {
                "individual_id": ind_id,
                "biosample_id": bs_id,
                "analysis_id": cs_id,
            }

            update_v = import_datatable_dict_line(update_v, fieldnames, v, "genomicVariant")
            update_v = ByconVariant().pgxVariant(update_v)
            update_v.update({
                "updated": datetime.now().isoformat()
            })
            vars_ided[cs_id].append(update_v)

        for cs_id, cs_vars in vars_ided.items():
            maps, cs_cnv_stats, cs_chro_stats, duplicates = GB.getAnalysisFracMapsAndStats(cs_vars)
            cs_ided[cs_id].update({"cnv_statusmaps": maps})
            cs_ided[cs_id].update({"cnv_stats": cs_cnv_stats})
            cs_ided[cs_id].update({"cnv_chro_stats": cs_chro_stats})
            cs_ided[cs_id].update({"updated": datetime.now().isoformat()})

        self.keyedBundle.update({
            "individuals_by_id": inds_ided,
            "biosamples_by_id": bios_ided,
            "analyses_by_id": cs_ided,
            "variants_by_analysis_id": vars_ided
        })


    #--------------------------------------------------------------------------#

    def __flatten_keyed_bundle(self):
        b_k_b = self.keyedBundle
        bios_k = b_k_b.get("biosamples_by_id", {})
        ind_k = b_k_b.get("individuals_by_id", {})
        cs_k = b_k_b.get("analyses_by_id", {})
        v_cs_k = b_k_b.get("variants_by_analysis_id", {})

        self.bundle.update({
            "biosamples": list( bios_k.values() ),
            "individuals": list( ind_k.values() ),
            "analyses": list( cs_k.values() ),
            "variants": [elem for sublist in ( v_cs_k.values() ) for elem in sublist]
        })


    #--------------------------------------------------------------------------#

    def __analysisBundleCreateIsets(self, label=""):
        # self.dataset_ids = list(set([cs.get("dataset_id", "NA") for cs in self.bundle["analyses"]]))
        GB = GenomeBins()
        for ds_id in self.datasets_results.keys():
            dscs = list(filter(lambda cs: cs.get("dataset_id", "NA") == ds_id, self.bundle["analyses"]))
            intervals, cnv_ana_count = GB.intervalFrequencyMaps(dscs)
            if cnv_ana_count < self.min_number:
                continue
            iset = {
                "dataset_id": ds_id,
                "group_id": ds_id,
                "label": label,
                "sample_count": cnv_ana_count,
                "interval_frequencies": []
            }
            for intv_i, intv in enumerate(intervals):
                iset["interval_frequencies"].append(intv.copy())
            prdbug(f'... __analysisBundleCreateIsets {ds_id} => sample_count {cnv_ana_count} ...')
            
            self.intervalFrequenciesBundles.append(iset)


    #--------------------------------------------------------------------------#

    def __fileAnalysisBundleCreateIsets(self, label=""):
        # self.dataset_ids = list(set([cs.get("dataset_id", "NA") for cs in self.bundle["analyses"]]))
        ds_id = "file"
        GB = GenomeBins()
        dscs = self.bundle["analyses"]
        intervals, cnv_ana_count = GB.intervalFrequencyMaps(dscs)
        iset = {
            "dataset_id": ds_id,
            "group_id": ds_id,
            "label": label,
            "sample_count": cnv_ana_count,
            "interval_frequencies": []
        }
        for intv_i, intv in enumerate(intervals):
            iset["interval_frequencies"].append(intv.copy())
        prdbug(f'... __analysisBundleCreateIsets {ds_id} => sample_count {cnv_ana_count} ...')
        
        self.intervalFrequenciesBundles.append(iset)


    #--------------------------------------------------------------------------#

    def __isetBundlesFromCollationParameters(self):
        fmap_name = "frequencymap"
        query = CollationQuery().getQuery()
 
        prdbug(f'... __isetBundlesFromCollationParameters query {query}')

        mongo_client = MongoClient(host=DB_MONGOHOST)
        for ds_id in self.datset_ids:
            coll_db = mongo_client[ds_id]
            for collation_f in coll_db["collations" ].find(query):
                if not (fmap := collation_f.get(fmap_name)):
                    continue
                fmap_count = fmap.get("frequencymap_samples", 0)
                if fmap_count < self.min_number:
                    continue
                r_o = {
                    "dataset_id": ds_id,
                    "group_id": collation_f.get("id", ""),
                    "label": re.sub(r';', ',', collation_f.get("label", "")),
                    "sample_count": fmap_count,
                    "frequencymap_samples": fmap.get("frequencymap_samples", fmap_count),
                    "interval_frequencies": fmap.get("intervals", [])
                }                    
                self.intervalFrequenciesBundles.append(r_o)
        mongo_client.close( )


################################################################################
