#!/usr/bin/env python3

from os import path
from bycon import *

loc_path = path.dirname( path.abspath(__file__) )
lib_path = path.join(loc_path , "lib")
sys.path.append( lib_path )
from importer_helpers import ByconautImporter

################################################################################
################################################################################
################################################################################

def main():
    initialize_bycon_service()
    BI = ByconautImporter()
    BI.update_individuals()


################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
