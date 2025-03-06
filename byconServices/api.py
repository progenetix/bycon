#!/usr/local/bin/python3

import json
from humps import camelize

from collections import OrderedDict
from bycon import BYC, prdbug, prjsonhead, prjsontrue, select_this_server

################################################################################

note = """
<hr/>
<b>
This page presents a prototype for an OpenAPI (Swagger) definition for the
<a href="https://genomebeacons.org" target="_blank">GA4GH Beacon API</a>. The definitions are generated from the
<a href="https://github.com/progenetix/bycon/tree/main/bycon/config" target="_blank">`entity_defaults` and `argument_definitions`</a>
in the <a href="https://bycon.progenetix.org" target="_blank">bycon project</a>.
</b>
<hr/>
The definitions are not yet complete. Please be aware that the whole capabilities
of the project cannot be represented solely through the OpenAPI definitions and also
involve features such as filtering terms logic and result aggregation across the different entities.
Additionally, the bycon project implements a number of data services beyong Beacon
standards which again are only partially covered here.
"""

def api():
    boapi = ByconOpenAPI()
    boapi.getAPI()

################################################################################
################################################################################
################################################################################

class ByconOpenAPI:
    def __init__(self):
        self.entity_defaults = BYC.get("entity_defaults", {})
        self.argument_definitions = BYC.get("argument_definitions", {}).get("$defs", {})
        self.this_server = select_this_server()

        self.beacon_eps = ["info", "dataset", "cohort", "genomicVariant", "analysis", "biosample", "individual", "filteringTerm"]
        self.service_eps = ["collations", "intervalFrequencies", "geolocations", "publications"]

        self.general_pars = ["skip", "limit", "requested_granularity"]

        info = self.entity_defaults.get("info", {}).get("content", {})

        self.oapi = OrderedDict({
            "openapi": "3.0.2",
            "servers": [ {"url": self.this_server } ],
            "info": {
                "title": info.get("name", "Progenetix Beacon API"),
                "version": info.get("version", ""),
                "description": info.get("description", "") + note,
                "contact": {"email": info.get("contact_url", "").replace("mailto:", "")}
            },
            "paths": {},
            "components": {
                "parameters": {}
            }
        })

        self.__add_beacon_paths()
        self.__add_service_paths()
        self.__add_component_parameters()

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def getAPI(self):
        prjsonhead()
        print(json.dumps(self.oapi, indent=2))


    # -------------------------------------------------------------------------#

    def saveAPI(self):
        # TODO - implement file export
        prjsonhead()
        print(json.dumps(self.oapi, indent=2))


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __add_beacon_paths(self):
        for e in self.beacon_eps:
            self.__add_entity_paths("beacon", e)


    # -------------------------------------------------------------------------#

    def __add_service_paths(self):
        for e in self.service_eps:
            self.__add_entity_paths("services", e)


    # -------------------------------------------------------------------------#

    def __add_entity_paths(self, path_part, entity):
        e_d = self.entity_defaults[entity]
        p = e_d.get("request_entity_path_id", None)
        r = e_d.get("response_entity_id", None)
        s = e_d.get("response_schema", None)
        rqp = e_d.get("response_entity_path_alias", p)

        pars = []
        if s == "beaconResultsetsResponse":
            for a, a_d in self.argument_definitions.items():
                if a_d.get("beacon_query"):
                    pars.append(a)

        entity_path = f"/{path_part}/{p}"
        self.oapi["paths"].update({
            entity_path: {"get": self.__path_create_get(r, rqp, r, s, pars)}
        })

        if s == "beaconResultsetsResponse":
            pars = ["id"]
            self.oapi["paths"].update({
                f"{entity_path}/{{id}}": {"get": self.__path_create_get(r, rqp, r, s, pars)}
            })

            # now for the retrieval of the other entities by this id, e.g.
            # `/analyses/{id}/g_variants`
            for b in self.beacon_eps:
                b_d = self.entity_defaults[b]
                b_s = b_d.get("response_schema", None)
                b_r = b_d.get("response_entity_id", None)
                b_p = b_d.get("request_entity_path_id", None)
                if b_s == "beaconResultsetsResponse" and b_r != r:
                    self.oapi["paths"].update({
                        f"{entity_path}/{{id}}/{b_p}": {"get": self.__path_create_get(r, rqp, b_r, b_s, pars)}
                    })

        if s != "beaconInfoResponse":
            for c_p in list(self.general_pars):
                self.oapi["paths"][entity_path]["get"]["parameters"].append({"$ref": f'#/components/parameters/{camelize(c_p)}'})


    # -------------------------------------------------------------------------#

    def __path_create_get(self, source_entity, response_entity_path_alias, target_entity, response_schema, pars):
        return {
            "summary": f"Get {target_entity} entries by {source_entity} id",
            "description": f"Get {target_entity} entries by {source_entity} id",
            "parameters": self.__add_parameters(pars, response_entity_path_alias),
            "responses": {
                "200": {
                    "description": f"An id response for {source_entity} entry",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": f"{self.this_server}/services/schemas/{response_schema}"
                            }
                        }
                    }
                }
            }
        }


    # -------------------------------------------------------------------------#

    def __add_parameters(self, pars, scope):
        path_pars = []
        for p in pars:
            if (p_d := self.argument_definitions.get(p)):
                path_pars.append(self.__format_parameter(camelize(p), p_d, scope))
        return path_pars


    # ------------------------------------------------------------------------ #

    def __format_parameter(self, parameter, definition, scope=None):
        p = {
            "name": parameter,
            "in": definition.get("in", "query"),
            "schema": {
                "type": definition.get("type", "string")
            }
        }
        if (i := definition.get("items")):
            p["schema"].update({"items": i})

        if len(e_s := definition.get("examples", [])) > 0:
            p.update({"examples":{}})
            for e in e_s:
                k = list(e.keys())[0]
                if (paths := e[k].get("in_paths")):
                    if scope in paths:
                        p["examples"].update(e)
                else:
                    p["examples"].update(e)

        return p

    # ------------------------------------------------------------------------ #
        
    def __add_component_parameters(self, pars=[]):
        for a, a_d in self.argument_definitions.items():
            if len(pars) > 0 and a not in pars:
                continue
            a_c = camelize(a)
            c_p = self.__format_parameter(a_c, a_d)
            self.oapi["components"]["parameters"].update({a_c: c_p})


# def __path_create_post(source_entity, response_entity_path_alias, target_entity, this_server, response_schema, par_def):
#     return  # {
            #     "summary": f"Post request for {r} entries",
            #     "description": f"Post request for {r} entries",
            #     "requestBody": {
            #         "content": {
            #             "application/json": {
            #                 "schema": {
            #                    "$ref": f'{this_server}/services/schemas/beaconRequestBody.json'
            #                 }
            #             }
            #         },
            #         "required": True
            #     },
            #     "responses": {
            #         "200": {
            #             "description": f"A {path_part} response for {r} entries",
            #             "content": {
            #                 "application/json": {
            #                     "schema": {
            #                         "$ref": f"{this_server}/services/schemas/{s}"
            #                     }
            #                 }
            #             }
            #         }
            #     }
            # }



################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    api()
