from mycgi import Form
from os import path
from uuid import uuid4

from bycon import BYC, print_json_response, select_this_server, print_uri_rewrite_response

################################################################################

def uploader():
    """
    This service is used by UI implementations to upload user provided `.pgxseg` files
    for visualization of the variants using the packages plotting functions.
    
    As exception to the general rule the `uploader` service does not make use of standard
    argument parsing but directly uses `cgi.FieldStorage()` and `....file.read()`.
    """
    file_id = str(uuid4())

    form_data = Form()
    fileitem = form_data['inputfile']
    filename = fileitem.filename
    data = fileitem.value
    base_url = select_this_server()

    response = {
        "error": {},
        "rel_path": f'{BYC["env_paths"].get("server_tmp_dir_web", "/tmp")}/{file_id}',
        "loc_path": path.join( *BYC["env_paths"][ "server_tmp_dir_loc" ], file_id ),
        "file_id": file_id,
        "plot_link": '/services/sampleplots/?fileId='+file_id,
        "host": base_url
    }

    if not filename:
        response.update({"error": "ERROR: No `inputfile` file parameter submitted ..." })
        print_json_response(response)

    response.update({
        "filename": filename,
        "data": data
    })

    with open(response["loc_path"], 'wb') as f:
        f.write(data)
    if not (plot_type := form_data.getvalue("plotType")):
        print_json_response(response)

    print_uri_rewrite_response(f'{base_url}/services/sampleplots/?datasetIds=upload&fileId={file_id}&plotType={plot_type}')
