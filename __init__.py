# __init__.py
from os import pardir, path
import sys

bycon_path = path.dirname( path.abspath(__file__) )
sys.path.append( bycon_path )

from beaconServer import *
from services import *
