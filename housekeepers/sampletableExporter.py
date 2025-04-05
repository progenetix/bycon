#!/usr/local/bin/python3

from bycon import *
from byconServiceLibs import ByconDatatableExporter, ByconDatatableExporter

fd = ByconResultSets().get_flattened_data()
ByconDatatableExporter(fd).export_datatable()
