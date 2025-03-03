#!/usr/local/bin/python3

import json
from collections import OrderedDict
from bycon import BYC, prdbug, prjsonhead, prjsontrue, select_this_server

################################################################################

"""
`api.py` generates OpenAPI definitions from the `entity_defaults` and
`services_entity_defaults`.

THIS IS A STUB AND NOT FUNCTIONAL YET
"""

e_d_s = BYC.get("entity_defaults", {})
info = e_d_s.get("info", {}).get("content", {})
this_server = select_this_server()

oapi = OrderedDict()

oapi["openapi"] = "3.0.2"
oapi["servers"] = [ this_server ]
oapi["info"] = {}
oapi["info"]["title"] = info.get("name", "Progenetix Beacon API")
for p in ["version", "description"]:
    oapi["info"][p] = info.get(p, "")
oapi["info"]["contact"] = {"email": info.get("contact_url", "").replace("mailto:", "")}
oapi["paths"] = {}
for e , e_d in e_d_s.items():
    p = e_d.get("request_entity_path_id", None)
    r = e_d.get("response_entity_id", None)
    oapi["paths"][f"/{p}"] = {
        "get": {
            "summary": f"Get {r} entries",
            "description": f"Get {r} entries",
            "responses": {
                "200": {
                    "description": f"List of {r} entries",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "array",
                                "items": {
                                    "$ref": f"{this_server}/services/schemas/{r}"
                                }
                            }
                        }
                    }
                }
            }
        }
    }



prjsonhead()
print(json.dumps(oapi, indent=2))
