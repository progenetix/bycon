#!/usr/local/bin/python3

from lib.service_response_generation import ByconServiceResponse
from byconplus import ByconImporter

BI = ByconImporter()
BI.import_records("biosample")
