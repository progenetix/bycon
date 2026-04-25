#!/usr/local/bin/python3

from os import pardir, path, sys

from lib.service_response_generation import ByconServiceResponse
from byconplus import ByconImporter

BI = ByconImporter()
BI.delete_records_and_downstream("analysis")
