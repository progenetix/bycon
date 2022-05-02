import argparse, os, yaml
from humps import decamelize

################################################################################

def get_bycon_args(byc):

	if not "local" in byc["env"]:
		return byc

	a_p = os.path.join( byc["pkg_path"], "config", "command_line_args.yaml" )
	with open( a_p ) as a_h:
		byc_cmd_args = yaml.load( a_h , Loader=yaml.FullLoader)

	parser = argparse.ArgumentParser()
	for d_k, defs in byc_cmd_args.items():
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
