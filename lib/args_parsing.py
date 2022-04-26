import argparse

from cgi_parsing import test_truthy
from filter_parsing import check_filter_values

################################################################################

def get_bycon_args(byc):

	parser = argparse.ArgumentParser()

	parser.add_argument("-e", "--entity", help="entity")
	parser.add_argument("-t", "--testMode", help="test setting")
	parser.add_argument("-f", "--filters", help="prefixed filter values, comma concatenated")

	byc.update({ "args": parser.parse_args() })

	return byc

################################################################################

def args_update_form(byc):

	if byc["args"].testMode is not None:
		byc["form_data"].update({"test_mode": test_truthy(byc["args"].testMode) })

	if byc["args"].entity is not None:
		byc.update({"request_entity_path_id": byc["args"].entity })

	if byc["args"].filters:
		f = byc["args"].filters.split(',')
		fs = check_filter_values(f, byc)
		if len(fs) > 0:
			byc["form_data"].update( { "filters": fs } )

	return byc

################################################################################
