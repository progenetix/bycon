import argparse, re

from humps import camelize, decamelize

from bycon_helpers import prdbug

################################################################################

def args_update_form(byc):
    """
    This function adds comand line arguments to the `byc["form_data"]` input
    parameter collection (in "local" context).
    """
    # Serves as "we've been here before" marker - before the env check.
    if byc.get("check_args", True) is False:
        return
    byc.update({"check_args": False})

    create_args_parser(byc)

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


