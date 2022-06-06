import argparse, os, yaml
from humps import decamelize

################################################################################

def get_bycon_args(byc, argdeffile=None):

	if byc.get("check_args", False) is False:
		return byc

	# Serves as "we've been here before" marker - before the env check.
	byc.update({"check_args": False})

	if not "local" in byc["env"]:
		return byc

	if argdeffile is None:
		argdeffile =  os.path.join( byc["pkg_path"], *byc["config"]["arg_defs_path"] )

	with open( argdeffile ) as a_h:
		argdefs = yaml.load( a_h , Loader=yaml.FullLoader)

	if byc["script_args"]:
		a_k_s = list(argdefs.keys())
		for a_d_k in a_k_s:
			if a_d_k not in byc["script_args"]:
				argdefs.pop(a_d_k, None)
	
	create_args_parser(byc, **argdefs)

	return byc

################################################################################

def create_args_parser(byc, **argdefs):

	if not "local" in byc["env"]:
		return byc

	parser = argparse.ArgumentParser()
	for d_k, defs in argdefs.items():
		parser.add_argument(*defs.pop("flags"), **defs)
	byc.update({ "args": parser.parse_args() })

	return byc

################################################################################

def args_update_form(byc):

	if not "local" in byc["env"]:
		return byc

	arg_vars = vars(byc["args"])

	for p in arg_vars.keys():
		if arg_vars[p] is None:
			continue
		p_d = decamelize(p)
		if p in byc["config"]["form_list_pars"]:
			byc["form_data"].update({p_d: arg_vars[p].split(',') })
		else:
			byc["form_data"].update({p_d: arg_vars[p]})

	return byc

################################################################################