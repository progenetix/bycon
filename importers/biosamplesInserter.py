#!/usr/local/bin/python3

from bycon import byconServiceLibs
from bycon_importer import ByconImporter

BI = ByconImporter()
BI.import_records("biosample")
