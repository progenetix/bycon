import argparse, humps, re

from bycon_helpers import prdbug, set_debug_state, test_truthy
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
    arg_vars = vars(cmd_args)
    for p in arg_vars.keys():
        if not (v := arg_vars.get(p)):
            continue
        p_d = humps.decamelize(p)
        if not (a_d := a_defs.get(p_d)):
            continue
        p_d_t = a_d.get("type", "string")
        if "array" in p_d_t:
            values = v.split(',')
            p_i_t = a_defs[p_d].get("items", "string")
            if "int" in p_i_t:
                BYC_PARS.update({p_d: list(map(int, values))})
            elif "number" in p_i_t:
                BYC_PARS.update({p_d: list(map(float, values))})
            else:
                BYC_PARS.update({p_d: list(map(str, values))})
        else:
            if "int" in p_d_t:
                BYC_PARS.update({p_d: int(v)})
            elif "number" in p_d_t:
                BYC_PARS.update({p_d: float(v)})
            elif "bool" in p_d_t:
                BYC_PARS.update({p_d: test_truthy(v)})
            else:
                BYC_PARS.update({p_d: str(v)})

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


