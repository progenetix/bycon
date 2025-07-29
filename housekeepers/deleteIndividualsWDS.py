#!/usr/local/bin/python3

from os import pardir, path, sys

#loc_path = path.dirname( path.abspath(__file__) )
#lib_path = path.join(loc_path , pardir, "importers", "lib")
#sys.path.append( lib_path )

from bycon import byconServiceLibs
from bycon_importer import ByconImporter

BI = ByconImporter()
BI.delete_records_and_downstream("individual")

