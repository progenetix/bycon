import argparse
import re

from cgi_parsing import prdbug
from humps import camelize, decamelize

################################################################################

def get_bycon_args(byc):
    if byc.get("check_args", True) is False:
        return

    # Serves as "we've been here before" marker - before the env check.
    byc.update({"check_args": False})

    if not "local" in byc.get("env", "server"):
        return byc

    create_args_parser(byc)


################################################################################

def create_args_parser(byc):
    if not "local" in byc.get("env", "server"):
        return

    a_defs = byc.get("argument_definitions")
    parser = argparse.ArgumentParser()
    for a_n, a_d in a_defs.items():
        if "cmdFlags" in a_d:
            argDef = {
                "flags": a_d.get("cmdFlags"),
                "help": a_d.get("description", "TBD"),
            }
            default = a_d.get("default")
            if default:
                argDef.update({"default": default})
            parser.add_argument(*argDef.pop("flags"), **argDef)

    byc.update({"args": parser.parse_args()})


################################################################################

def args_update_form(byc):
    """
    This function adds comand line arguments to the `byc["form_data"]` input
    parameter collection (in "local" context).
    """
    if not "args" in byc:
        return
    if not "local" in byc.get("env", "server"):
        return

    a_defs = byc["argument_definitions"]
    list_pars = []
    for a_n, a_d in a_defs.items():
        if "cmdFlags" in a_d:
            a_d_k = camelize(a_n)
            if "array" in a_d.get("type", "string"):
                list_pars.append(a_d_k)

    arg_vars = vars(byc["args"])

    for p in arg_vars.keys():
        if arg_vars[p] is None:
            continue
        p_d = decamelize(p)
        if p in list_pars:
            byc["form_data"].update({p_d: arg_vars[p].split(',')})
        else:
            byc["form_data"].update({p_d: arg_vars[p]})
        prdbug(f'{p}: {byc["form_data"][p_d]}', byc.get("debug_mode"))


################################################################################

def filters_from_args(byc):
    if not "args" in byc:
        return

    if not "filters" in byc:
        byc.update({"filters": []})

    if byc["args"].filters:
        for f in re.split(",", byc["args"].filters):
            byc["filters"].append({"id": f})


################################################################################

def set_collation_types(byc):
    
    if byc["args"].collationTypes:
        s_p = {}
        for p in re.split(",", byc["args"].collationTypes):
            if p in byc["filter_definitions"].keys():
                s_p.update({p: byc["filter_definitions"][p]})
        if len(s_p.keys()) < 1:
            print("No existing collation type was provided with `--collationTypes` ...")
            exit()
        byc.update({"filter_definitions": s_p})


################################################################################

def set_processing_modes(byc):
    byc.update({"update_mode": False})

    tm = byc.get("test_mode", False)
    env = byc.get("env", "server")

    if not "local" in env:
        return

    if byc["test_mode"] is True:
        print("¡¡¡ TEST MODE - no db update !!!")
        return

    if byc["args"].update:
        byc.update({"update_mode": True})
        print("¡¡¡ UPDATE MODE - may overwrite entries !!!")



