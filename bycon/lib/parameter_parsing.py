import argparse, humps, json, re, sys
from mycgi import Form
from urllib.parse import urlparse, unquote
from os import environ
from pymongo import MongoClient

from bycon_helpers import prdbug, prdbughead, test_truthy
from config import *

################################################################################

class ByconParameters:
    def __init__(self):
        self.arg_defs = BYC["argument_definitions"].get("$defs", {})
        self.no_value = NO_PARAM_VALUES
        self.byc_pars = {}
        self.request_uri = environ.get('REQUEST_URI', False)
        self.request_type = "__none__"
        self.request_meta = {}
        self.request_query = {}

        self.__detect_request_environment()

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def get_definitions(self):
        return self.arg_defs


    # -------------------------------------------------------------------------#

    def set_parameters(self):
        self.__process_parameters()
        BYC_PARS.update(self.byc_pars)
        return self.byc_pars


    # -------------------------------------------------------------------------#

    def rest_path_value(self, key=""):
        """
        This function splits the path of the REQUEST_URI and returns the path element
        after a provided key. The typical uise case would be to get the entity or
        executing script, or an {id} value from a REST path e.g.

        * `/beacon/biosamples/?` => "beacon" -> "biosamples"
        * `/services/cytomapper/?` => "services" -> "cytomapper"
        * `/services/intervalFrequencies/NCIT:C3072/` => "intervalFrequencies" -> "NCIT:C3072"

        """
        if not self.request_uri:
            return
        url_comps = urlparse(self.request_uri)
        p_items = re.split('/', url_comps.path)
        p_items = [x for x in p_items if len(x) > 1]
        p_items = [x for x in p_items if not "debugMode" in x]

        for i, p in enumerate(p_items, 1):
            if len(p_items) > i:
                if unquote(p) in [key, f'{key}.py', unquote(key)]:
                    return unquote(p_items[i])
            elif p == key:
                return None
        return None


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __detect_request_environment(self):
        if "___shell___" in ENV:
            self.request_type = "SHELL"
        elif "POST" in environ.get('REQUEST_METHOD', ''):
            self.request_type = "POST"
        else:
            self.request_type = "GET"


    # -------------------------------------------------------------------------#

    def __process_parameters(self):
        self.__arguments_set_defaults()
        self.__pars_from_path()
        self.__pars_from_shell()
        self.__pars_from_POST()
        self.__pars_from_GET()
        self.__set_debug_mode()


    # -------------------------------------------------------------------------#

    def __arguments_set_defaults(self):
        for a, d in self.arg_defs.items():
            if "default" in d:
                self.byc_pars.update({a: d["default"]})
            if "local" in d and self.request_type == "SHELL":
                self.byc_pars.update({a: d["local"]})


    # -------------------------------------------------------------------------#

    def __pars_from_path(self):
        """
        The function deparses a Beacon REST path into its components and assigns
        those to the respective variables. The assumes structure is:

        `__root__/__request_entity_path_id__/__path_parameter__/__response_entity_path_id__/?query...`
            |             |                     |                   |
        "beacon"  e.g. "biosamples"     "pgxbs-t4ee3"   e.g. "genomicVariations"
            |             |                     |                   |
        required      required              optional            optional
        """

        if not self.request_uri:
            return

        url_comps = urlparse(self.request_uri)
        url_p = url_comps.path
        p_items = re.split('/', url_p)

        if not REQUEST_PATH_ROOT in p_items:
            return

        p_items = list(filter(None, p_items))
        p_len = len(p_items)
        r_i = p_items.index(REQUEST_PATH_ROOT)

        if p_len == r_i + 1:
            self.byc_pars.update({"request_entity_path_id": "info"})
            return

        for p_k in ["request_entity_path_id", "path_ids", "response_entity_path_id"]:
            r_i += 1
            if r_i >= p_len:
                break
            p_v = unquote(p_items[r_i])
            if p_v.lower() in self.no_value:
                break
            self.byc_pars.update({p_k: p_v})

        if (rpidv := self.byc_pars.get("path_ids")):
            self.byc_pars.update({"path_ids": rpidv.split(",") })


    # -------------------------------------------------------------------------#

    def __pars_from_shell(self):
        """
        This function adds comand line arguments to the input
        parameter collection in a "local" context.
        """
        if self.request_type != "SHELL":
            return

        parser = argparse.ArgumentParser()
        for a_n, a_d in self.arg_defs.items():
            if "cmdFlags" in a_d:
                argDef = {
                    "flags": a_d.get("cmdFlags"),
                    "help": a_d.get("description", "TBD"),
                }
                # TODO: This seems like a re-processing of defaults
                if (default := a_d.get("default")):
                    argDef.update({"default": default})
                parser.add_argument(*argDef.pop("flags"), **argDef)
        cmd_args = parser.parse_args()
        arg_vars = vars(cmd_args)

        for p in arg_vars.keys():
            if not (v := arg_vars.get(p)):
                continue
            if str(v).lower() in self.no_value:
                continue
            p_d = humps.decamelize(p)
            if not (a_d := self.arg_defs.get(p_d)):
                continue
            values = str(v).split(',')
            p_v = RefactoredValues(a_d).refVal(values)
            if p_v or p_v == 0:
                self.byc_pars.update({p_d: p_v})


    # -------------------------------------------------------------------------#

    def __pars_from_POST(self):
        if self.request_type != "POST":
            return

        content_len = environ.get('CONTENT_LENGTH', '0')
        content_typ = environ.get('CONTENT_TYPE', '')

        # TODO: catch error & return for non-json posts
        if not "json" in content_typ:
            return

        body = sys.stdin.read(int(content_len))
        jbod = json.loads(body)

        self.request_meta.update(jbod.get("meta", {}))
        self.request_query.update(jbod.get("query", {}))

        self.__POST_parse_meta()
        self.__POST_parse_query()


    # -------------------------------------------------------------------------#

    def __POST_parse_meta(self):
        BYC.update({"request_meta": self.request_meta})


    # -------------------------------------------------------------------------#

    def __POST_parse_query(self):
        for p, v in self.request_query.items():

            p_d = humps.decamelize(p)

            if p == "filters":
                self.byc_pars.update({p: v})
                continue

            if p == "requestParameters":
                for rp, rv in v.items():
                    rp_d = humps.decamelize(rp)

                    if "datasets" in rp:
                        if (ds_ids := rv.get("datasetIds")):
                            self.byc_pars.update({"dataset_ids": ds_ids})

                    elif "g_variant" in rp_d:
                        for vp, vv in v[rp].items():
                            vp_d = humps.decamelize(vp)
                            if vp_d in self.arg_defs:
                                self.byc_pars.update({vp_d: vv})

                    elif "variant_multi_pars" in rp_d:
                        vmp = []
                        for v_p_s in rv:
                            varp = {}
                            for vp, vv in v_p_s.items():
                                vp_d = humps.decamelize(vp)
                                if vp_d in self.arg_defs:
                                    varp.update({vp_d: vv})
                            vmp.append(varp)
                        self.byc_pars.update({rp_d: vmp})

                    elif rp_d in self.arg_defs:
                        self.byc_pars.update({rp_d: rv})

                continue

            if p == "pagination":
                for p_k in ["skip", "limit"]:
                    if p_k in v:
                        self.byc_pars.update({p_k: v[p_k]})
                continue

            if p_d in self.arg_defs:
                self.byc_pars.update({p_d: v})
            else:
                w_m = f'!!! Unmatched parameter {p}: {v}'
                BYC["WARNINGS"].append(w_m)
                prdbug(f'!!! Unmatched parameter {p}: {v}')


    # -------------------------------------------------------------------------#

    def __pars_from_GET(self):
        if self.request_type != "GET":
            return

        self.form_data = Form()
        for p in self.form_data:
            p_d = humps.decamelize(p)
            # CAVE: Only predefined parameters are accepted!
            if (a_d := self.arg_defs.get(p_d)):
                p_type = a_d.get("type", "string")
                values = self.__form_return_listvalue(p, p_type)
                v = RefactoredValues(a_d).refVal(values)
                if v or v == 0:
                    self.byc_pars.update({p_d: v})
                    prdbug(f'__pars_from_GET: {p_d} =>> {v}')
            else:
                w_m = f'!!! Unmatched parameter {p}: {self.form_data.getvalue(p)}'
                BYC["WARNINGS"].append(w_m)
                prdbug(f'!!! Unmatched parameter {p}: {self.form_data.getvalue(p)}')


    # -------------------------------------------------------------------------#

    def __form_return_listvalue(self, p, p_type):
        """
        This function returns a list of values from a form data object. Additionally
        it performs an explicit merge-split cycle on the values which have a
        `type: array` definition in `argument_definitions` to ensure that e.g. multi-value
        versions in GET requests are correctly processed.
        """
        l_v = []

        v = self.form_data.getlist(p)
        for n_v in ["null", "undefined", "None"]:
            if n_v in v: v.remove(n_v)
        if len(v) < 1: return l_v

        if "array" in p_type:
            l_v = ','.join(v)
            l_v = l_v.split(',')
        else:
            l_v = v
        return l_v


    # -------------------------------------------------------------------------#

    def __set_debug_mode(self):
        debug = self.byc_pars.get("debug_mode", False)
        if BYC["DEBUG_MODE"] is True:
            debug = True
        if test_truthy(debug):
            BYC.update({"DEBUG_MODE": True})
            if self.request_type != "SHELL":
                print('Content-Type: text')
                print()


################################################################################

class ByconFilters:
    def __init__(self):
        self.filter_defs = BYC["filter_definitions"].get("$defs", {})
        self.filter_patterns = [f.get("pattern") for f in self.filter_defs.values()]
        self.filter_pars = BYC_PARS.get("filters", [])
        self.parsed_filters = []
        self.__parse_filters()

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def get_filters(self):
        return self.parsed_filters


    # -------------------------------------------------------------------------#

    def get_filter_ids(self):
        return [x.get("id") for x in self.parsed_filters]


    # -------------------------------------------------------------------------#

    def get_filters_string(self):
        return ",".join(list(str(x.get("id")) for x in self.parsed_filters))


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __parse_filters(self):
        """
        The function checks the filter values for a match to any of the filter
        definitions. The optional `!` flag (no match) is not considered during
        evaluation ("deflagged").
        This filter check is complementary to the evaluation during the filter query
        generation and provides a warning if the filter pattern doesn't exist.
        """
        checked_ids = []
        for f in self.filter_pars:
            if not isinstance(f, dict):
                f = {"id": f}
            if not "id" in f:
                continue
            deflagged = re.sub(r'^!', '', f["id"])
            matched = False
            for f_p in self.filter_patterns:
                if re.compile(f_p).match(deflagged):
                    matched = True
                    continue
            if matched is False:
                BYC["WARNINGS"].append( f'The filter {f["id"]} does not match any defined filter pattern.')
            if f["id"] in checked_ids:
                continue
            checked_ids.append(str(f["id"]))
            self.parsed_filters.append(f)


################################################################################
################################################################################
################################################################################

class ByconEntities:
    def __init__(self):
        self.entity_defaults = BYC.get("entity_defaults", {})
        self.arg_defs = BYC["argument_definitions"].get("$defs", {})
        self.dealiased_path_ids = {}
        self.request_entity_path_id = None
        self.response_entity_path_id = None
        self.request_path_id_par = BYC_PARS.get("request_entity_path_id", "___none___")
        self.response_path_id_par = BYC_PARS.get("response_entity_path_id", "___none___")
        self.path_ids = BYC_PARS.get("path_ids", False)
        self.request_entity_id = None
        self.response_entity_id = None
        self.response_entity = {}

        self.__map_entity_aliases()
        self.__assign_entities()
        self.__path_ids_to_pars()

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def set_entities(self):
        BYC.update({
            "request_entity_path_id": self.request_entity_path_id,
            "request_entity_id": self.request_entity_id,
            "response_entity_id": self.response_entity_id,
            "response_entity": self.response_entity,
            "response_schema": self.response_entity.get("response_schema", "beaconInfoResponse"),
            "bycon_response_class": self.response_entity.get("bycon_response_class", "BeaconInfoResponse")
        })

    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __map_entity_aliases(self):
        """
        The default entyity id is mapped to the path id and its aliases.
        """
        for e, e_d in self.entity_defaults.items():
            if (p_id := e_d.get("request_entity_path_id")):
                self.dealiased_path_ids.update({p_id: e})
            for p_a_s in e_d.get("request_entity_path_aliases", []):
                self.dealiased_path_ids.update({p_a_s: e})
        if self.request_path_id_par in self.dealiased_path_ids.keys():
            self.request_entity_path_id = self.request_path_id_par
        else:
            self.request_entity_path_id = "info" 

        """
        A response_path_id is assigned if a separate response path was provided
        """
        if self.response_path_id_par in self.dealiased_path_ids.keys():
            self.response_entity_path_id = self.response_path_id_par


    # -------------------------------------------------------------------------#

    def __assign_entities(self):
        # entity retrieval from path ids
        self.request_entity_id = self.dealiased_path_ids.get(self.request_entity_path_id)
        # get entity definitions 
        self.request_entity = self.entity_defaults.get(self.request_entity_id)
        # re-assign the default path
        if (dp := self.request_entity.get("request_entity_path_id")):
            self.request_entity_path_id = dp

        if not self.response_entity_path_id:
            # in byconServices there are default standard entitys for some requests
            if (rpid := self.request_entity.get("response_entity_path_alias")):
                self.response_entity_path_id = rpid
            else:
                # fallback to the standard "no different response entity" case
                self.response_entity_path_id = self.request_entity_path_id


        self.response_entity_id = self.dealiased_path_ids.get(self.response_entity_path_id)
        self.response_entity = self.entity_defaults.get(self.response_entity_id)


    # -------------------------------------------------------------------------#

    def __path_ids_to_pars(self):
        p_p = self.request_entity.get("path_id_value_bycon_parameter", "id")
        if (rpidv := self.path_ids):
            if p_p in self.arg_defs.keys():
                v = RefactoredValues(self.arg_defs[p_p]).refVal(rpidv)
                BYC_PARS.update({p_p: v})


################################################################################
################################################################################
################################################################################

class ByconDatasets:
    def __init__(self):
        self.dataset_defs = BYC.get("dataset_definitions", {})
        self.dataset_ids = []
        self.database_names = []
        self.allow_default = True

        self.__get_database_names()
        self.__ds_ids_from_rest_path_value()
        # self.__ds_ids_from_record_id()
        self.__ds_ids_from_accessid()
        self.__ds_ids_from_form()
        self.__ds_ids_from_all_datasets()
        self.__ds_ids_from_default()

        ds_ids = self.dataset_ids


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def get_dataset_ids(self):
        return self.dataset_ids


    # -------------------------------------------------------------------------#

    def set_dataset_ids(self):
        BYC.update({"BYC_DATASET_IDS": self.dataset_ids})


    # -------------------------------------------------------------------------#

    def get_database_names(self):
        return self.database_names


    # -------------------------------------------------------------------------#
    # ----------------------------- private ------------------------------------#
    # -------------------------------------------------------------------------#

    def __get_database_names(self):
        if "DATABASE_NAMES" in environ:
          self.database_names = environ["DATABASE_NAMES"].split()
        else:
          try:
            mongo_client = MongoClient(host=DB_MONGOHOST)
            db_names = list(mongo_client.list_database_names())
            self.database_names = [x for x in db_names if x not in [HOUSEKEEPING_DB, SERVICES_DB, "admin", "config", "local"]]
          except Exception as e:
            BYC["WARNINGS"].append(f'Could not connect to MongoDB:\n####\n{e}\n####')


    # -------------------------------------------------------------------------#

    def __ds_ids_from_rest_path_value(self):
        if len(self.dataset_ids) > 0:
            return
        if not (ds_p_id := ByconParameters().rest_path_value("datasets")):
            return

        for ds_id in ds_p_id.split(","):
            if ds_id in self.database_names:
                self.dataset_ids.append(ds_id)


    # -------------------------------------------------------------------------#

    def __ds_ids_from_record_id(self):
        """
        For data retrieval associated with a single record by its path id such as
        `biosamples/{id}` the default Beacon model does not provide any way to provide
        the associated dataset id with the request. The assumption is that any record
        id is unique across all datasets.
        This function is a placeholder for a solution:
        * retrieve the dataset id from the record id, e.g. by having a specific prefix
          or pattern in the record id, associated for a specific dataset (a bit of a fudge...)
        * access a lookup database for the id -> datasetId matches
        """
        return


    # -------------------------------------------------------------------------#

    def __ds_ids_from_accessid(self):
        if len(self.dataset_ids) > 0:
            return
        # TODO: This is very verbose. In principle there should be an earlier
        # test of existence...

        if not (accessid := BYC_PARS.get("accessid")):
            return

        ho_client = MongoClient(host=DB_MONGOHOST)
        h_o = ho_client[HOUSEKEEPING_DB][HOUSEKEEPING_HO_COLL].find_one({"id": accessid})
        if not h_o:
            return
        ds_id = h_o.get("ds_id", False)
        if (ds_id := str(h_o.get("ds_id"))) not in self.database_names:
            return
        self.dataset_ids = [ds_id]


    # -------------------------------------------------------------------------#

    def __ds_ids_from_form(self):
        if len(self.dataset_ids) > 0:
            return
        if not (f_ds_ids := BYC_PARS.get("dataset_ids")):
            return
        ds_ids = [ds for ds in f_ds_ids if ds in self.database_names]
        if len(ds_ids) > 0:
            self.dataset_ids = ds_ids
        else:
            BYC["ERRORS"].append(f"!!! The requested dataset id(s) {f_ds_ids} do not match any of the available datasets.")
            prdbug(f"!!! The dataset id(s) {f_ds_ids} do not match any of the available datasets.")


    # -------------------------------------------------------------------------#

    def __ds_ids_from_all_datasets(self):
        if len(self.dataset_ids) > 0:
            return
        if not "dataset" in BYC.get("response_entity_id", "___none___"):
            return
        self.dataset_ids = list(BYC["dataset_definitions"].keys())


    # -------------------------------------------------------------------------#

    def __ds_ids_from_default(self):
        if len(self.dataset_ids) > 0:
            return
        if self.allow_default is False:
            return
        defaults: object = BYC["beacon_defaults"].get("defaults", {})  
        if (ds_id := str(defaults.get("default_dataset_id"))) not in self.database_names:
            return
        self.dataset_ids =  [ds_id]


################################################################################
################################################################################
################################################################################

class RefactoredValues():
    def __init__(self, parameter_definition={}):
        self.v_list = []
        self.v_string = ""
        self.parameter_definition = parameter_definition
        self.join_by = parameter_definition.get("split_by", "&&")

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def refVal(self, vs=[]):
        if type(vs) != list:
            vs = [vs]
        self.v_list = vs
        self.__refactor_values_from_defined_type()

        return self.v_list


    # -------------------------------------------------------------------------#

    def strVal(self, vs=""):
        if type(vs) != list:
            vs = [vs]
        self.v_list = vs
        self.__stringify_values_from_defined_type()
        return self.v_string


    # -------------------------------------------------------------------------#
    # ----------------------------- private ------------------------------------#
    # -------------------------------------------------------------------------#

    def __stringify_values_from_defined_type(self):
        defs = self.parameter_definition

        values = self.v_list

        if len(values) == 0:
            self.v_list = None
            return

        if "array" in defs.get("type", "string"):
            # remapping definitions to the current item definitions
            defs = self.parameter_definition.get("items", {"type": "string"})
        p_t = defs.get("type", "string")

        v_l = []
        for v in values:
            v_l.append(self.__cast_string(defs, v))

        self.v_string = str(self.join_by.join(v_l))


    # -------------------------------------------------------------------------#

    def __refactor_values_from_defined_type(self):
        p_d_t = self.parameter_definition.get("type", "string")
        values = list(x for x in self.v_list if x is not None)
        values = list(x for x in values if str(x).lower() not in ["none", "null", "undefined"])

        if len(values) == 0:
            self.v_list = None
            return

        defs = self.parameter_definition
        if "array" in p_d_t:
            # remapping definitions to the current item definitions
            defs = self.parameter_definition.get("items", {"type": "string"})

        v_l = []
        for v in values:
            v_l.append(self.__cast_type(defs, v))
        if "array" in p_d_t:
            self.v_list = v_l
            return

        # testing against the input values; ==0 already checked
        if len(values) == 1:
            self.v_list = v_l[0]
            return

        if self.parameter_definition.get("forceNoSplit"):
            self.v_list = ",".join(v_l)
            return

        BYC["WARNINGS"].append(f"!!! Multiple values ({','.join(values)}) for {p_d_t} in request")
        return


    # -------------------------------------------------------------------------#

    def __cast_string(self, defs, p_value):
        p_type = defs.get("type", "string")
        if "object" in p_type:
            return self.__object_to_string(defs, p_value)
        if "array" in p_type:
            if type(p_value) != list:
                p_value = [p_value]
            return self.join_by.join(p_value)
        return str(p_value)


    # -------------------------------------------------------------------------#

    def __cast_type(self, defs, p_value):
        p_type = defs.get("type", "string")
        if "object" in p_type:
            return self.__split_string_to_object(defs, p_value)
        if "int" in p_type:
            return int(p_value)
        if "number" in p_type:
            return float(p_value)
        if "bool" in p_type:
            return test_truthy(p_value)
        if len(en := defs.get("enum", [])) > 0:
            prdbug(f'... {p_value} in {en}')
            if str(p_value) in en:
                return str(p_value)
            return None
        return str(p_value)


    # -------------------------------------------------------------------------#

    def __split_string_to_object(self, defs, value):
        o_p = defs.get("parameters", ["id", "label"])
        o_s = defs.get("split_by", "::")
        t_s = defs.get("types", [])
        if len(t_s) != len(o_p):
            t_s = ["string"] * len(o_p)
        o = {}
        for v_i, v_v in enumerate(value.split(o_s)):
            if "int" in t_s[v_i] and re.match(r'^\d+?$', v_v):
                v_v = int(v_v)
            elif "num" in t_s[v_i] and re.match(r'^\d+?(\.\d+?)?$', v_v):
                v_v = float(v_v)
            o.update({o_p[v_i]: v_v})
        return o


    # -------------------------------------------------------------------------#

    def __object_to_string(self, defs, value):
        if type(value) != dict:
            return ""
        o_p = defs.get("parameters", ["id", "label"])
        o_s = defs.get("split_by", "::")
        s_l = []
        for k in o_p:
            s_l.append(str(value.get(k, "")))
        return o_s.join(s_l)


