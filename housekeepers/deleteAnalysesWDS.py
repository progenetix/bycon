#!/usr/local/bin/python3

from os import pardir, path, sys

from bycon import byconServiceLibs
from bycon_importer import ByconImporter

BI = ByconImporter()
BI.delete_records_and_downstream("analysis")
