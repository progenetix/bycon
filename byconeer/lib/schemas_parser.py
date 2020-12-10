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

