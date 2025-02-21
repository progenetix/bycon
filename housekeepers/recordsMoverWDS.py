#!/usr/local/bin/python3

from os import pardir, path
# from bycon import *

loc_path = path.dirname( path.abspath(__file__) )
lib_path = path.join(loc_path , pardir, "importers", "lib")
sys.path.append( lib_path )
from bycon_importer import ByconImporter

"""
The `recordsMoverWDS.py` script is used to move records from a source database
(indicated with `-d`) to a target database (indicated with `--output`). It requires
the use of a tab-separated file with the record `individual_id` identifiers to be moved.

* ./housekeepers/recordsMoverWDS.py -d progenetix --output cellz -i ./imports/1kdeltest.tsv --testMode false
"""

BI = ByconImporter()
BI.move_individuals_and_downstream()
