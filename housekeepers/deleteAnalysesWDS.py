#!/usr/local/bin/python3

from os import pardir, path, sys

from bycon import byconServiceLibs
from importer_helpers import ByconautImporter

BI = ByconautImporter()
BI.delete_analyses_and_downstream()
