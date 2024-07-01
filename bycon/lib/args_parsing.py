import argparse, humps, re

from bycon_helpers import prdbug, refactor_value_from_defined_type, set_debug_state, test_truthy
from config import *

################################################################################

def args_update_form():
    """
    This function adds comand line arguments to the `BYC_PARS` input
    parameter collection (in "local" context).
    """
    a_defs = BYC.get("argument_definitions", {})
    cmd_args = __create_args_parser(a_defs)
    arg_vars = vars(cmd_args)
    for p in arg_vars.keys():
        if not (v := arg_vars.get(p)):
            continue
        p_d = humps.decamelize(p)
        if not (a_d := a_defs.get(p_d)):
            continue
        values = str(v).split(',')
        p_v = refactor_value_from_defined_type(p, values, a_defs[p_d])
        if p_v is not None:
            BYC_PARS.update({p_d: p_v})

    BYC.update({"DEBUG_MODE": set_debug_state(BYC_PARS.get("debug_mode", False)) })


################################################################################

def __create_args_parser(a_defs):
    parser = argparse.ArgumentParser()
    for a_n, a_d in a_defs.items():
        if "cmdFlags" in a_d:
            argDef = {
                "flags": a_d.get("cmdFlags"),
                "help": a_d.get("description", "TBD"),
            }
            if (default := a_d.get("default")):
                argDef.update({"default": default})
            parser.add_argument(*argDef.pop("flags"), **argDef)
    cmd_args = parser.parse_args()
    return cmd_args


