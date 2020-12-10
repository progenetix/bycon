import re, json, yaml
from os import path, scandir

################################################################################

def read_schema_files(**byc):

	schemas = { }

	s_path = path.join( byc["pkg_path"], "byconeer", "config", "schemas" )
	s_files = [ f.path for f in scandir() if f.is_file() ]
	s_files = [ f for f in s_files if f.endswith(".yaml") ]

	for s_f in s_files:
		with open( s_f ) as s_f_h:
        	s = yaml.load( s_f_h , Loader=yaml.FullLoader)
        	schemas.update( { s["title"]: s["properties"] } )

    return schemas

################################################################################

def create_db_schema(schemaname, **schemas):

	coll_s = { }

	s_n = schemaname # TODO: convert to PascalCase
	s = schemas[ s_n ]

	for s_p, s_s in s.items():
		n = s_p # TODO: convert to snake_case
		n_v = True # just a placeholder
		# adding the proper empty property values
		# the $ref ones should be accessible through schemas[ s_p ]

		coll_s = update( { n: n_v })

	return coll_s
