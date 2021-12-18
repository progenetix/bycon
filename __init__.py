# __init__.py
from os import pardir, path
import sys

dir_path = path.dirname( path.abspath(__file__) )
sys.path.append( dir_path )

from beaconServer import *
from services import *
