import csv, re, requests, sys
from os import path
from pymongo import MongoClient

# bycon
from bycon import (
    BYC,
    BYC_PARS,
    DB_MONGOHOST,
    RefactoredValues,
    prdbug,
    prdlhead,
    prjsonnice
)

services_lib_path = path.join(path.dirname(path.abspath(__file__)))
sys.path.append(services_lib_path)
from file_utils import ExportFile


################################################################################

class ByconDatatableExporter:
    def __init__(self, data=[]):
        self.datatable_mappings = BYC.get("datatable_mappings", {"$defs": {}})
        self.entity = BYC.get("response_entity_id", "___none___")
        if not self.entity in self.datatable_mappings["$defs"]:
            # TODO: proper error handling
            return

        self.data = data

        sel_pars = BYC_PARS.get("delivery_keys", [])      
        io_params = self.datatable_mappings["$defs"][self.entity]["parameters"]
        if len(sel_pars) > 0:
            io_params = { k: v for k, v in io_params.items() if k in sel_pars }

        self.io_params = io_params


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def stream_datatable(self, file_type=None):
        self.file_name = f'{self.entity}.tsv'
        prdlhead(self.file_name)
        print(f'{self.__create_table_header()}\n')
        for pgxdoc in self.data:
            print(f'{self.__table_line_from_pgxdoc(pgxdoc)}\n')


    # -------------------------------------------------------------------------#

    def export_datatable(self, file_type=None):
        if not (table_file := ExportFile().check_outputfile_path()):
            prdbug(ExportFile().check_outputfile_path())
            return

        t_f = open(table_file, "w")
        t_f.write(f'{self.__create_table_header()}\n')
        for pgxdoc in self.data:
            t_f.write(f'{self.__table_line_from_pgxdoc(pgxdoc)}\n')
        t_f.close()


    # -------------------------------------------------------------------------#
    # ---------------------------- private ------------------------------------#
    # -------------------------------------------------------------------------#

    def __table_line_from_pgxdoc(self, pgxdoc):
        line = []
        for par, par_defs in self.io_params.items():
            parameter_type = par_defs.get("type", "string")
            db_key = par_defs.get("db_key", "___undefined___")
            v = get_nested_value(pgxdoc, db_key)
            line.append(RefactoredValues(par_defs).strVal(v))
        return "\t".join( line )

    # -------------------------------------------------------------------------#

    def __create_table_header(self):
        """
        """
        header_labs = [ ]
        for par, par_defs in self.io_params.items():
            pres = par_defs.get("prefix_split", {})
            if len(pres.keys()) < 1:
                header_labs.append( par )
                continue
            for pre in pres.keys():
                header_labs.append( par+"_id"+"___"+pre )
                header_labs.append( par+"_label"+"___"+pre )

        return "\t".join(header_labs)


################################################################################
################################################################################
################################################################################

def import_datatable_dict_line(parent, fieldnames, lineobj, primary_scope="biosample"):
    dt_m = BYC["datatable_mappings"]
    if not primary_scope in dt_m["$defs"]:
        return
    io_params = dt_m["$defs"][ primary_scope ]["parameters"]
    for f_n in fieldnames:
        if "#"in f_n:
            continue
        if f_n not in io_params.keys():
            continue
        if not (par_defs := io_params.get(f_n, {})):
            continue
        if not (dotted_key := par_defs.get("db_key")):
            continue
        p_type = par_defs.get("type", "string")

        v = lineobj[f_n].strip()
        if v.lower() in (".", "na"):
            v = ""
        if v.startswith("{") and v.endswith("}"):
            v = ""
        if len(v) < 1:
            if f_n in io_params.keys():
                v = io_params[f_n].get("default", "")
        if len(v) < 1:
            continue

        # prdbug(f'Importing {f_n} with value: {v}')

        # special case for geolocations
        if "geoprov_id" in f_n:
            add_geolocation_to_pgxdoc(parent, v)
            continue

        # this makes only sense for updating existing data; if there would be
        # no value, the parameter would just be excluded from the update object
        # if there was an empy value
        if v.lower() in ("___delete___", "__delete__", "none", "___none___", "__none__", "-"):
            if "array" in p_type:
                v = []
            elif "object" in p_type:
                v = {}
            else:
                v = ""
        else:
            split_by = par_defs.get("split_by", "&&")
            v = RefactoredValues(par_defs).refVal(v.split(split_by))

        assign_nested_value(parent, dotted_key, v, par_defs)

    return parent


################################################################################

def assign_nested_value(parent, dotted_key, v, parameter_definitions={}):
    parameter_type = parameter_definitions.get("type", "string")

    if not v and v != 0:
        if not (v := parameter_definitions.get("default")):
            return parent

    if "array" in parameter_type:
        if type(v) is not list:
            v = v.split(',')
    elif "num" in parameter_type:
        if str(v).strip().lstrip('-').replace('.','', 1).isdigit():
            v = float(v)
    elif "integer" in parameter_type:
        if str(v).strip().isdigit():
            v = int(v)
    elif "string" in parameter_type:
        v = str(v)

    ps = dotted_key.split('.')

    if len(ps) == 1:
        parent.update({ps[0]: v })
        return parent

    if ps[0] not in parent or parent[ ps[0] ] is None:
        parent.update({ps[0]: {}})
    if len(ps) == 2:
        parent[ ps[0] ].update({ps[1]: v })
        return parent
    if  ps[1] not in parent[ ps[0] ] or parent[ ps[0] ][ ps[1] ] is None:
        parent[ ps[0] ].update({ps[1]: {}})
    if len(ps) == 3:
        parent[ ps[0] ][ ps[1] ].update({ps[2]: v })
        return parent
    if  ps[2] not in parent[ ps[0] ][ ps[1] ] or parent[ ps[0] ][ ps[1] ][ ps[2] ] is None:
        parent[ ps[0] ][ ps[1] ].update({ps[2]: {}})
    if len(ps) == 4:
        parent[ ps[0] ][ ps[1] ][ ps[2] ].update({ps[3]: v })
        return parent
    
    if len(ps) > 4:
        print("¡¡¡ Parameter key "+dotted_key+" nested too deeply (>4) !!!")
        return '_too_deep_'

    return parent

################################################################################

def get_nested_value(parent, dotted_key, parameter_type="string"):
    ps = str(dotted_key).split('.')
    v = ""

    if len(ps) == 1:
        try:
            v = parent[ ps[0] ]
        except:
            v = ""
    elif len(ps) == 2:
        try:
            v = parent[ ps[0] ][ ps[1] ]
        except:
            v = ""
    elif len(ps) == 3:
        try:
            v = parent[ ps[0] ][ ps[1] ][ ps[2] ]
        except:
            v = ""
    elif len(ps) == 4:
        try:
            v = parent[ ps[0] ][ ps[1] ][ ps[2] ][ ps[3] ]
        except:
            v = ""
    elif len(ps) == 5:
        try:
            v = parent[ ps[0] ][ ps[1] ][ ps[2] ][ ps[3] ][ ps[4] ]
        except:
            v = ""
    elif len(ps) > 5:
        print("¡¡¡ Parameter key "+dotted_key+" nested too deeply (>5) !!!")
        return '_too_deep_'

    return v

################################################################################

def add_geolocation_to_pgxdoc(pgxdoc, geoprov_id):
    """
    Adds a geolocation to a pgxdoc by its ID.
    """
    if not geoprov_id:
        return pgxdoc

    if not "::" in geoprov_id:
        return pgxdoc

    mongo_client = MongoClient(host=DB_MONGOHOST)
    geo_info = mongo_client["_byconServicesDB"]["geolocs"].find_one({"id": geoprov_id}, {"_id": 0, "id": 0})
    if geo_info is None:
        return pgxdoc
    pgxdoc.update({"geo_location": geo_info.get("geo_location", {})})
    pgxdoc["geo_location"]["properties"].update({"geoprov_id": geoprov_id})
    mongo_client.close()

    return pgxdoc

