import re

from pymongo import MongoClient

from bycon import (
    BYC,
    BYC_PARS,
    DB_MONGOHOST,
    mongo_and_or_query_from_list,
    prdbug,
    rest_path_value
)

class OntologyMaps:
    def __init__(self):
        self.query = {}
        self.term_groups = []
        self.unique_terms = []
        self.filters = BYC.get("BYC_FILTERS", [])
        self.filter_definitions = BYC.get("filter_definitions", {})
        # TODO: Shouldn't be hard coded here
        self.filter_id_matches = ["NCIT", "pgx:icdom", "pgx:icdot", "UBERON"]

        self.__ontologymaps_query()

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def ontology_maps_query(self):
        return self.query


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def ontology_maps_results(self):
        self.__retrieve_ontologymaps()
        return [
            { 
                "term_groups": self.term_groups,
                "unique_terms": self.unique_terms
            }
        ]


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __ontologymaps_query(self):
        if (p_filter := rest_path_value("ontologymaps")):
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
        mongo_client = MongoClient(host=DB_MONGOHOST)
        mongo_coll = mongo_client["_byconServicesDB"]["ontologymaps"]
        for o in mongo_coll.find( self.query, { '_id': False } ):
            for c in o["code_group"]:
                pre, code = re.split("[:-]", c["id"], maxsplit=1)
                u_c_d.update( { c["id"]: { "id": c["id"], "label": c["label"] } } )
            self.term_groups.append( o["code_group"] )
        mongo_client.close( )

        for k, u in u_c_d.items():
            self.unique_terms.append(u)        



        if "termGroups" in BYC["response_entity_id"]:
            t_g_s = []
            for tg in self.term_groups:
                t_l = []
                for t in tg:
                    t_l.append(str(t.get("id", "")))
                    t_l.append(str(t.get("label", "")))
                t_g_s.append("\t".join(t_l))

            if "text" in BYC_PARS.get("output", "___none___"):
                print_text_response("\n".join(t_g_s))
            results = c_g



