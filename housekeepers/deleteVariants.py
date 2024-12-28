#!/usr/local/bin/python3

from os import pardir, path, sys

loc_path = path.dirname( path.abspath(__file__) )
lib_path = path.join(loc_path , pardir, "importers", "lib")
sys.path.append( lib_path )
from importer_helpers import ByconautImporter

BI = ByconautImporter()
BI.delete_variants_of_analyses()
