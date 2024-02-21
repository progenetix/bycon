import argparse, humps, re

from bycon_helpers import prdbug, set_debug_state
from config import *

################################################################################

def args_update_form(byc):
    """
    This function adds comand line arguments to the `BYC_PARS` input
    parameter collection (in "local" context).
    """
    # Serves as "we've been here before" marker - before the env check.
    if byc.get("check_args", True) is False:
        return
    byc.update({"check_args": False})

    a_defs = byc["argument_definitions"]
    cmd_args = create_args_parser(a_defs)
    list_pars = []
    for a_n, a_d in a_defs.items():
        if "cmdFlags" in a_d:
            a_d_k = humps.camelize(a_n)
            if "array" in a_d.get("type", "string"):
                list_pars.append(a_d_k)
    arg_vars = vars(cmd_args)
    for p in arg_vars.keys():
        if not arg_vars[p]:
            continue
        p_d = humps.decamelize(p)
        if p in list_pars:
            BYC_PARS.update({p_d: arg_vars[p].split(',')})
        else:
            BYC_PARS.update({p_d: arg_vars[p]})

    BYC.update({"DEBUG_MODE": set_debug_state(BYC_PARS.get("debug_mode", False)) })


################################################################################

def create_args_parser(a_defs):
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
    cmd_args = parser.parse_args()
    return cmd_args


