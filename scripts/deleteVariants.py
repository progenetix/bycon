#!/usr/local/bin/python3

from lib.service_response_generation import ByconServiceResponse
from byconplus import ByconImporter

BI = ByconImporter()
BI.delete_variants_of_analyses()
