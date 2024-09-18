#!/usr/bin/env python3
import cgi, re, sys, traceback
from os import environ, path
from uuid import uuid4

from bycon import *

services_conf_path = path.join( path.dirname( path.abspath(__file__) ), "config" )
services_lib_path = path.join( path.dirname( path.abspath(__file__) ), "lib" )
sys.path.append( services_lib_path )
from bycon_bundler import ByconBundler
from bycon_plot import *
from interval_utils import generate_genome_bins
from service_helpers import read_service_prefs

################################################################################
################################################################################
################################################################################

def main():
    try:
        uploader()
    except Exception:
        print_text_response(traceback.format_exc(), 302)


################################################################################

def uploader():
    initialize_bycon_service()
    read_service_prefs("uploader", services_conf_path)
    file_id = str(uuid4())
    form_data = cgi.FieldStorage()
    base_url = select_this_server()

    response = {
        "error": {},
        "rel_path": f'{BYC["local_paths"].get("server_tmp_dir_web", "/tmp")}/{file_id}',
        "loc_path": path.join( *BYC["local_paths"][ "server_tmp_dir_loc" ], file_id ),
        "file_id": file_id,
        "plot_link": '/services/sampleplots/?fileId='+file_id,
        "host": base_url
    }

    if not "upload_file" in form_data:
        response.update({"error": "ERROR: No `upload_file` parameter in POST..." })
        print_json_response(response)

    file_item = form_data["upload_file"]
    file_name = path.basename(file_item.filename)
    file_type = file_name.split('.')[-1]
    data = file_item.file.read()

    response.update({
        "file_name": file_name,
        "file_type": file_type
    })

    with open(response["loc_path"], 'wb') as f:
        f.write(data)
    if not "plotType" in form_data:
        print_json_response(response)

    plot_type = form_data["plotType"]
    print_uri_rewrite_response(f'{base_url}/services/sampleplots/?datasetIds=upload&fileId={file_id}&plotType={plot_type}', "")


################################################################################
################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
