#!/usr/local/bin/python3

from bycon import BYC, prjsonnice
from bycon.byconServiceLibs import ask_limit_reset, assertSingleDatasetOrExit, OntologyMaps

ask_limit_reset()
assertSingleDatasetOrExit()
OM = OntologyMaps()
ontology_maps = OM.replace_ontology_maps()
erroneous_maps = OM.retrieve_erroneous_maps()
if BYC["TEST_MODE"] is True:
    for o in erroneous_maps:
        prjsonnice(o)
print(f'==>> {len(erroneous_maps)} have errors')
