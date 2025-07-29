import humps, re, json

from json_ref_dict import RefDict, materialize
from os import path, scandir, pardir
from pathlib import Path

from bycon_helpers import prjsonnice, prdbug
from config import *

################################################################################

class RecordsHierarchy:
    """This class provides hierarchy methods for the main data entities which are
    applied e.g. during query execution and record insertion and update processes.
    """

    def __init__(self):
        self.record_entities = ["individual", "biosample", "analysis", "genomicVariant"]

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def entities(self):
        return self.record_entities


    # -------------------------------------------------------------------------#

    def downstream(self, entity="___none___"):
        ds = []
        if entity not in self.record_entities:
            return ds
        now = False
        for e in self.record_entities:
            if now:
                ds.append(e)
            if e == entity:
                now = True
        return ds


    # -------------------------------------------------------------------------#

    def upstream(self, entity="___none___"):
        us = []
        if entity not in self.record_entities:
            return us
        now = True
        for e in self.record_entities:
            if e == entity:
                now = False
            if now:
                us.append(e)
        return us


################################################################################

class ByconSchemas:
    def __init__(self, schema_name="", root_key=""):
        self.entity_defaults = BYC.get("entity_defaults", {})
        self.schemas_root = Path(path.join(PKG_PATH, "schemas"))
        self.schema_files = []
        self.schema_def = {}
        self.schema_instance = {}
        self.schema_name = schema_name
        self.schema_path_id = schema_name
        self.root_key = root_key
        self.ext = "json"
        self.schema_path = False

        # TODO: commented out since on 2025-07-04 in bycon the
        # `bycon-model/__request_entity_path_id__/defaultSchema.yaml`
        # was replaced with `bycon-model/__request_entity_id__.yaml`
        # if self.schema_name in self.entity_defaults:
        #     if (r_p_id := self.entity_defaults[self.schema_name].get("request_entity_path_id")):
        #         self.schema_path_id = r_p_id

        self.__retrieve_schema_file_path()


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def get_schema_instance(self):
        self.read_schema_file()
        self.__create_empty_instance()
        return self.schema_instance


    # -------------------------------------------------------------------------#

    def read_schema_file(self):
        # some lookup for the `request_entity_path_id` value in the case of "true"
        # entry types where schemas are defined in a directory with the path id

        if self.schema_path is not False:
            if len(self.root_key) > 1:
                self.schema_path += f'#/{self.root_key}'
            root_def = RefDict(self.schema_path)   
            exclude_keys = [ "examples" ] #"format",
            self.schema_instance = materialize(root_def, exclude_keys=exclude_keys)
            assert isinstance(self.schema_instance, dict)
            return self.schema_instance

        return False


    # -------------------------------------------------------------------------#

    def get_schema_file_path(self):
        return self.schema_path


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __retrieve_schema_file_path(self):
        # self.__get_default_schema_file_path()
        self.__get_schema_file_path()


    # -------------------------------------------------------------------------#

    # def __get_default_schema_file_path(self):
    #     f_n = f'defaultSchema.{self.ext}'
    #     s_p_s = [ f for f in self.schemas_root.rglob("*") if f.is_file() ]
    #     s_p_s = [ f for f in s_p_s if f.name == f_n ]
    #     s_p_s = [ f for f in s_p_s if f.parent.name == self.schema_path_id ]
    #     if len(s_p_s) == 1:
    #         self.schema_path = f'{s_p_s[0].resolve()}'


    # -------------------------------------------------------------------------#

    def __get_schema_file_path(self):
        f_n = f'{self.schema_name}.{self.ext}'
        s_p_s = [ f for f in self.schemas_root.rglob("*") if f.is_file() ]
        s_p_s = [ f for f in s_p_s if f.name == f_n ]
        if len(s_p_s) == 1:
            self.schema_path = f'{s_p_s[0].resolve()}'


    # -------------------------------------------------------------------------#

    def __create_empty_instance(self):
        self.schema_instance = self.__instantiate_schema(self.schema_instance)
        self.schema_instance = humps.decamelize(self.schema_instance)


    # -------------------------------------------------------------------------#

    def __instantiate_schema(self, schema_part):
        if 'type' in schema_part:
            if schema_part['type'] == 'object' and 'properties' in schema_part:
                empty_dict = {}
                for prop, prop_schema in schema_part['properties'].items():
                    empty_dict[prop] = self.__instantiate_schema(prop_schema)
                return empty_dict
            elif schema_part['type'] == 'array' and 'items' in schema_part:
                return [self.__instantiate_schema(schema_part['items'])]
            elif "const" in schema_part:
                return schema_part.get("const", "")
            elif "default" in schema_part:
                return schema_part["default"]

        return {}
      
