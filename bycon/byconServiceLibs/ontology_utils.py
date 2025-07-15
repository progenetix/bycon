import re
from random import sample as random_samples
from progress.bar import Bar

from pymongo import MongoClient

from bycon import *

# from bycon import (
#     BYC,
#     BYC_PARS,
#     ByconFilters,
#     ByconParameters,
#     DB_MONGOHOST,
#     mongo_and_or_query_from_list,
#     prdbug,
#     prjsonnice
# )

class OntologyMaps:
    """
    The `OntologyMaps` class is used to create, retrieve and store ontology maps,
    i.e. the corresponding terms for codes from different ontologies or controlled
    vocabularies. In the context of the Progenetix Beacon as a data-rich `bycon`
    deployment, a particlular use is the mapping of codes from different cancer
    related diagnostic codes, specifically from ICD-O 3 histology/topography doublets
    with NCIt cancer codes.
    """
    def __init__(self):
        self.query = {}
        self.term_groups = []
        self.unique_terms = []
        self.ontology_maps = []
        self.erroneous_maps = []
        self.filters = ByconFilters().get_filters()
        self.filter_definitions = BYC["filter_definitions"].get("$defs", {})
        # TODO: Shouldn't be hard coded here
        self.filter_id_matches = ["NCIT", "pgx:icdom", "pgx:icdot", "UBERON"]
        self.ds_id = BYC["BYC_DATASET_IDS"][0]

        self.ontologymaps_coll = MongoClient(host=DB_MONGOHOST)["_byconServicesDB"]["ontologymaps"]
        self.bios_coll = MongoClient(host=DB_MONGOHOST)[self.ds_id]["biosamples"]

        self.combos = [
            {
                "icdom": "icdo_morphology",
                "icdot": "icdo_topography",
                "NCIT": "histological_diagnosis"
            },
            {
                "icdot": "icdo_topography",
                "UBERON": "sample_origin_detail"
            }
        ]

        self.__ontologymaps_query()

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def ontology_maps_query(self):
        return self.query


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def ontology_maps_results(self):
        if len(self.query.keys()) < 1:
            BYC["ERRORS"].append("No correct filter value provided!")
        else:
            self.__retrieve_ontologymaps()

        return [
            { 
                "term_groups": self.term_groups,
                "unique_terms": self.unique_terms
            }
        ]


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def replace_ontology_maps(self):
        self.__create_ontology_maps()
        if BYC["TEST_MODE"] is True:
            for o in self.ontology_maps:
                prjsonnice(o)
            print(f'==>> {len(self.ontology_maps)} maps would be created')
            return self.ontology_maps
        self.ontologymaps_coll.delete_many({})
        for o in self.ontology_maps:
            self.ontologymaps_coll.insert_one(o)
        o_c = self.ontologymaps_coll.count_documents({})
        print(f'==>> {o_c} maps have been created in the database')
        return self.ontology_maps
 

    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def retrieve_erroneous_maps(self):
        if len(self.ontology_maps) < 1:
            self.__create_ontology_maps()
        return self.erroneous_maps
 

    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __ontologymaps_query(self):
        if (p_filter := ByconParameters().rest_path_value("ontologymaps")):
            self.filters.append({"id": p_filter})
        q_list = [ ]
        q_dups = [ ]
        pre_re = re.compile(r'^(\w+?)([:-].*?)?$')
        for f in self.filters:
            if not (f_val := f.get("id")):
                continue
            if not pre_re.match(f_val):
                continue
            pre = pre_re.match( f_val ).group(1)
            if f_val in self.filter_id_matches:
                pre = f_val
                BYC_PARS.update({"filter_precision": "start"})
            else:
                BYC_PARS.update({"filter_precision": "exact"})
            for f_t, f_d in self.filter_definitions.items():
                if not re.compile(f_d["pattern"]).match(f_val):
                    continue
                if f_val in q_dups:
                    continue
                q_dups.append(f_val)
                if "start" in BYC_PARS.get("filter_precision", "exact"):
                    q_list.append( { "code_group.id": { "$regex": f'^{f_val}' } } )
                elif f["id"] == pre:
                    q_list.append( { "code_group.id": { "$regex": f'^{f_val}' } } )
                else:
                    q_list.append( { "code_group.id": f_val } )

        self.query = mongo_and_or_query_from_list(q_list, "AND")


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __retrieve_ontologymaps(self):
        u_c_d = { }
        for o in self.ontologymaps_coll.find( self.query, { '_id': False } ):
            for c in o["code_group"]:
                pre, code = re.split("[:-]", c["id"], maxsplit=1)
                u_c_d.update( { c["id"]: { "id": c["id"], "label": c["label"] } } )
            self.term_groups.append( o["code_group"] )

        for k, u in u_c_d.items():
            self.unique_terms.append(u)        

        # if "termGroups" in BYC["response_entity_id"]:
        #     t_g_s = []
        #     for tg in self.term_groups:
        #         t_l = []
        #         for t in tg:
        #             t_l.append(str(t.get("id", "")))
        #             t_l.append(str(t.get("label", "")))
        #         t_g_s.append("\t".join(t_l))

        #     if "text" in BYC_PARS.get("output", "___none___"):
        #         print_text_response("\n".join(t_g_s))
        #     results = c_g


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __create_ontology_maps(self):
        keyed_maps = {}
        bios_no = self.bios_coll.count_documents({})

        for c in self.combos:
            map_type = "::".join(c.keys())
            print(f'Re-generating {map_type} ontology maps from {bios_no} samples...')
            bar = Bar(f'Processing {bios_no} from {self.ds_id}', max = bios_no, suffix='%(percent)d%%' )
            for bios in self.bios_coll.find({}, { '_id': False }).limit(BYC_PARS.get("limit", 0)):
                bar.next()
                ids = []
                qs = {}
                cg = []
                errors = []
                for k, v in c.items():
                    o_re = re.compile(self.filter_definitions.get(k, {}).get("pattern", "___none___"))
                    o = bios.get(v, {"id": "___none___", "label": "___none___"})
                    oid = o.get("id")
                    ids.append(str(oid))
                    qs.update({f'{v}.id': oid})
                    cg.append(o)
                    if not o_re.match(str(oid)):
                        errors.append(f'{v}.id: {oid}')
                uid = "::".join(ids)
                if uid in keyed_maps.keys():
                    continue
                keyed_maps.update({
                    uid: {
                        "id": uid,
                        "map_type": map_type,
                        "code_group": cg,
                        "local_query": qs,
                        "examples": [],
                        "errors": errors
                    }
                })
            bar.finish()

        for k, v in keyed_maps.items():
            examples = self.bios_coll.distinct("notes", v["local_query"])
            s_no = min(10, len(examples))
            e = random_samples(examples, s_no)
            e = [t for t in e if len(t) > 2]
            v.update({"examples": e})
            if len(v.get("errors", 0)) > 0:
                self.erroneous_maps.append(v)
                continue
            self.ontology_maps.append(v)

