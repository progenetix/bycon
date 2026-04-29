#!/usr/local/bin/python3

# loc_path = path.dirname( path.abspath(__file__) )
# lib_path = path.join(loc_path , pardir, "importers", "lib")
# sys.path.append( lib_path )

from byconplus import ByconImporter

BI = ByconImporter()
BI.delete_records_and_downstream("individual")
