#!/usr/bin/env python3

from os import pardir, path
# from bycon import *

loc_path = path.dirname( path.abspath(__file__) )
lib_path = path.join(loc_path , pardir, "importers", "lib")
sys.path.append( lib_path )
from importer_helpers import ByconautImporter

"""
./housekeepers/recordsMoverWDS.py -d progenetix --output cellz -i ./imports/1kdeltest.tsv --testMode false
"""

BI = ByconautImporter()
BI.move_individuals_and_downstream()
