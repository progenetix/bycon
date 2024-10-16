#!/usr/bin/env python3

from os import pardir, path, sys
from bycon import initialize_bycon_service

loc_path = path.dirname( path.abspath(__file__) )
lib_path = path.join(loc_path , pardir, "importers", "lib")
sys.path.append( lib_path )
from importer_helpers import ByconautImporter

################################################################################

def main():
    initialize_bycon_service()
    BI = ByconautImporter()
    BI.delete_individuals_and_downstream()


################################################################################

if __name__ == '__main__':
    main()
