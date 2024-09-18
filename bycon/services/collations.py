#!/usr/bin/env python3

import re, sys, traceback
from os import path, environ, pardir
from pymongo import MongoClient

from bycon import *

services_conf_path = path.join( path.dirname( path.abspath(__file__) ), "config" )
services_lib_path = path.join( path.dirname( path.abspath(__file__) ), "lib" )
sys.path.append( services_lib_path )
from service_response_generation import *
from service_helpers import read_service_prefs

################################################################################
################################################################################
################################################################################

def main():
    try:
        collations()
    except Exception:
        print_text_response(traceback.format_exc(), 302)
    
################################################################################

def collations():
    initialize_bycon_service()
    read_service_prefs("collations", services_conf_path)
    r = ByconautServiceResponse()
    print_json_response(r.collationsResponse())


################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
