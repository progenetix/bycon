# __init__.py
import sys, traceback
from os import environ, path
from pathlib import Path

from bycon.config import HTTP_HOST

services_lib_path = path.dirname( path.abspath(__file__) )
sys.path.append( services_lib_path )

try:
    from service_response_generation import *

except Exception:
    if not "___shell___" in HTTP_HOST:
        print('Content-Type: text/plain')
        print('status: 302')
        print()
    print(traceback.format_exc())
    print()
    exit()
