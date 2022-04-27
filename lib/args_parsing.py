import argparse, os
from humps import decamelize

from cgi_parsing import test_truthy
from filter_parsing import check_filter_values

################################################################################

def get_bycon_args(byc):

	parser = argparse.ArgumentParser()

	parser.add_argument("-e", "--requestEntityPathId", help="request_entity_path_id", default="biosamples")
	parser.add_argument("--requestedSchema", help="requested schema")

	parser.add_argument("-t", "--testMode", help="test setting, i.e. returning some random documents")
	parser.add_argument("-o", "--output", help="special output format; command line processing uses some predefined text as standard, but options are e.g. json or pgxseg", default="text")
	parser.add_argument("-l", "--limit", help="limit number of documents", default=0)

	parser.add_argument("--filters", help="prefixed filter values, comma concatenated")
	parser.add_argument("--filterPrecision", help="exact or start", default="exact")

	parser.add_argument("--assemblyId", help="assembly id")
	parser.add_argument("--referenceName", help="chromosome")
	parser.add_argument("--start", help="genomic start position")
	parser.add_argument("--end", help="genomic end position")
	parser.add_argument("--variantType", help="variant type, e.g. DUP")
	parser.add_argument("--referenceBases", help="reference bases")
	parser.add_argument("--alternateBases", help="alternate bases")
	parser.add_argument("--variantMinLength", help="variantMinLength")
	parser.add_argument("--variantMaxLength", help="variantMaxLength")
	parser.add_argument("--geneId", help="gene id")

	parser.add_argument("--cytoBands", help="cytobands, e.g. 8q21q24.1")
	parser.add_argument("--chroBases", help="only for the cytoband converter ... e.g. 8:0-120000000")

	parser.add_argument("--city", help="only for the geolocations...")
	parser.add_argument("--geoLatitude", help="only for the geolocations...")
	parser.add_argument("--geoLongitude", help="only for the geolocations...")
	parser.add_argument("--geoDistance", help="only for the geolocations...")

	byc.update({ "args": parser.parse_args() })

	return byc

################################################################################

def args_update_form(byc):

	if not "local" in byc["env"]:
		return byc

	arg_vars = vars(byc["args"])

	special = ["requestEntityPathId"]

	for p in arg_vars.keys():
		if arg_vars[p] is None:
			continue
		if p in special:
			continue
		p_d = decamelize(p)
		if p in byc["config"]["form_list_pars"]:
			byc["form_data"].update({p_d: arg_vars[p].split(',') })
		else:
			byc["form_data"].update({p_d: arg_vars[p]})

	if byc["args"].requestEntityPathId is not None:
		byc.update({"request_entity_path_id": byc["args"].requestEntityPathId })

	return byc

################################################################################
