#!/usr/local/bin/python3

import json, yaml
from humps import camelize
from markdown import markdown as md
from os import path

from collections import OrderedDict

from bycon import BYC, BYC_PARS, ByconFilteringTerms, ChroNames, load_yaml_empty_fallback, prdbug, prjsonhead, prjsontrue, select_this_server

services_conf_path = path.join( path.dirname( path.abspath(__file__) ), "config" )

################################################################################

note = """
This page presents a prototype for an OpenAPI (Swagger) definition for the
[GA4GH Beacon API](https://genomebeacons.org"). The definitions are generated
from the [`entity_defaults` and `argument_definitions`](https://github.com/progenetix/bycon/tree/main/bycon/config)
in the [**bycon project**](https://bycon.progenetix.org). The definitions are not
yet complete. Please be aware that the whole capabilities of the project cannot
be represented solely through the OpenAPI definitions and also involve features
such as filtering terms and result aggregation across the different entities.
Additionally, the bycon project implements a number of data services beyong Beacon
standards which again are only partially covered here.

#### `bycon` and Data Aggregation

The Beacon standard implements a REST style syntax - e.g. consistent id-based document retrieval
for entities indicated through their entry path - but is not _explicit_
regarding result aggregation following queries. The `bycon`
framework provide full data aggregation; _i.e._ queries with parameters against
*any* of the main data entities (g_variants, runs, analyses, biosamples, infividuals) will return results from all entities, with the
results representing an intersection of the query results at the level of the response
entity.

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
        self.examples = load_yaml_empty_fallback(path.join(services_conf_path, "examples.yaml"))
        self.argument_definitions = BYC.get("argument_definitions", {}).get("$defs", {})
        self.mode = BYC_PARS.get("mode", "__none__")
        self.this_server = select_this_server()

        self.beacon_eps = ["info", "dataset", "cohort", "genomicVariant", "analysis", "biosample", "individual", "filteringTerm"]
        self.service_eps = ["collations", "intervalFrequencies", "geolocations", "publications"]
        self.collation_types = ["NCIT", "pubmed", "NCITsex", "icdom"]
        self.general_pars = ["skip", "limit", "requested_granularity"]

        self.include_id_paths = True
        self.get_parameter_values = True

        info = self.entity_defaults.get("info", {}).get("content", {})

        self.oapi = OrderedDict({
            "openapi": "3.0.2",
            "servers": [ {"url": self.this_server } ],
            "info": {
                "title": info.get("name", "Progenetix Beacon API"),
                "version": info.get("version", ""),
                "description": f'<p>{info.get("description", "")}</p>{md(note)}',
                "contact": {"email": info.get("contact_url", "").replace("mailto:", "")}
            },
            "paths": {},
            "components": {
                "parameters": {}
            }
        })

        self.__add_example_links()
        self.__modify_by_mode()
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

    def __add_example_links(self):
        e_l = []
        for e, e_d in self.examples.items():
            l = e_d.get("label", e)
            h = e_d.get("link", e)
            if len(h) > 0:
                h = f'mode={h}'
            e_l.append(f'<a href="?{h}">[{l}]</a>')
        self.oapi["info"]["description"] += f'<hr/><b>{" | ".join(e_l)}</b><hr/>'


    # -------------------------------------------------------------------------#

    def __modify_by_mode(self):
        if not (e := self.examples.get(self.mode)):
            self.mode = False
            return
        
        # if entities are defined -> all defaults are ignored
        if (e_s := e.get("entities")):
            self.beacon_eps = e_s
            self.service_eps = []

        self.include_id_paths = False
        self.get_parameter_values = False

        pars = {}
        for k, e_v in e.get("example_values", {}).items():
            pars.update({k: self.argument_definitions[k]})
            pars[k]["examples"] = e_v
        for p in self.general_pars:
            pars.update({p: self.argument_definitions[p]})

        self.argument_definitions = pars


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
        c = e_d.get("bycon_response_class", "BeaconInfoResponse")
        rqp = e_d.get("response_entity_path_alias", p)

        pars = []
        if s == "beaconResultsetsResponse":
            for a, a_d in self.argument_definitions.items():
                if self.mode:
                    if "VQS" in self.mode:
                        if a_d.get("vqs_query"):
                            pars.append(a)
                    else:
                        if a_d.get("beacon_query"):
                            pars.append(a)
                elif a_d.get("beacon_query"):
                    pars.append(a)

        entity_path = f"/{path_part}/{p}"
        self.oapi["paths"].update({
            entity_path: self.__path_add_methods(p, rqp, r, s, pars)
        })

        if s == "beaconResultsetsResponse" and self.include_id_paths is True:
            pars = ["id"]
            self.oapi["paths"].update({
                f"{entity_path}/{{id}}": self.__path_add_methods(p, rqp, r, s, pars)
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
                        f"{entity_path}/{{id}}/{b_p}": self.__path_add_methods(p, rqp, b_r, b_s, pars)
                    })

        if "BeaconDataResponse" in c:
            if  "parameters" in self.oapi["paths"][entity_path]["get"]:
                for c_p in list(self.general_pars):
                    self.oapi["paths"][entity_path]["get"]["parameters"].append({"$ref": f'#/components/parameters/{camelize(c_p)}'})


    # -------------------------------------------------------------------------#

    def __path_add_methods(self, entity_path_id, response_entity_path_alias, target_entity, response_schema, pars):
        if self.mode:
            tag = self.mode
        elif entity_path_id in self.service_eps:
            tag = "Services"
        else:
            tag = "Beacon"
        schema_link = f"{self.this_server}/services/schemas/{response_schema}"
        r = {"get": self.__path_create_get(tag, response_entity_path_alias, target_entity, schema_link, pars)}
        if response_schema == "beaconResultsetsResponse":
            r.update({"post": self.__path_create_post(tag, target_entity, schema_link)})

        if not "service-info" in entity_path_id:
            r["get"]["responses"].update({
                "default": {
                    "description": "An unsuccessful operation.",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": f'{self.this_server}/services/schemas/beaconErrorResponse'
                            }
                        }
                    }
                }
            })

        return r


    # -------------------------------------------------------------------------#

    def __path_create_get(self, tag, response_entity_path_alias, target_entity, schema_link, pars):
        # TODO: pre-define schemas and update the copy here
        return {
            "summary": f"Get {target_entity} entries",
            "description": f"Get {target_entity} entries",
            "tags": [f'{tag}'],
            "parameters": self.__add_parameters(pars, response_entity_path_alias),
            "responses": {
                "200": {
                    "description": f"A response for {target_entity} entries",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": schema_link
                            }
                        }
                    }
                },
                "default": {
                    "description": "An unsuccessful operation.",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": f'{self.this_server}/services/schemas/beaconErrorResponse'
                            }
                        }
                    }
                }
            }
        }


    # -------------------------------------------------------------------------#


    def __path_create_post(self, tag, target_entity, schema_link):
        # TODO: pre-define schemas and update the copy here
        return {
            "summary": f"Post request for {target_entity} entries",
            "description": f"Post request for {target_entity} entries",
            "tags": [f'{tag}'],
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                           "$ref": f'{self.this_server}/services/schemas/beaconRequestBody'
                        }
                    }
                },
                "required": True
            },
            "responses": {
                "200": {
                    "description": f"A response for {target_entity} entries",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": schema_link
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
                path_pars.append(self.__format_parameter(p, p_d, scope))
        return path_pars


    # ------------------------------------------------------------------------ #

    def __format_parameter(self, parameter, definition, scope=None):
        p = {
            "name": camelize(parameter),
            "in": definition.get("in", "query"),
            "schema": {
                "type": definition.get("type", "string")
            }
        }

        for d_k in ["items", "minItems", "maxItems"]:
            if (i := definition.get(d_k)):
                p["schema"].update({d_k: i})

        return self.__parameter_add_examples(p, parameter, definition, scope)


    # ------------------------------------------------------------------------ #

    def __parameter_add_examples(self, p, parameter, definition, scope):

        e_s = definition.get("examples", [])
        e_s += self.__parameter_get_values(parameter)

        if len(e_s) < 1:
            return p

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
            c_p = self.__format_parameter(a, a_d)
            self.oapi["components"]["parameters"].update({camelize(a): c_p})


    # ------------------------------------------------------------------------ #

    def __parameter_get_values(self, par):
        vals = []
        if self.get_parameter_values is False:
            return vals
        if par in ["reference_name", "mate_name"]:
            r_l = ChroNames().refseqLabeled()
            for c in r_l:
                k = list(c.keys())[0]
                v = list(c.values())[0]
                vals.append({
                    v:{
                        "value": k,
                        "summary": f'{v} ({k})'
                    }
                })

        elif par in ["variant_type"]:
            for v_t, v_d in BYC.get("variant_type_definitions").items():
                if not v_d.get("beacon_query", True):
                    continue
                vals.append({
                    v_t:{
                        "value": v_t,
                        "summary": f'{v_t} ({v_d.get("variant_state", {}).get("label", "")})'
                    }
                })

        elif par == "filters":
            # TODO: This is a temporary solution to get some random filters using
            #       the TEST_MODE settings.
            BYC.update({"response_entity_id": "filteringTerm", "TEST_MODE": True})
            BYC_PARS.update({"test_mode_count": 10})
            f_t_s = ByconFilteringTerms().filteringTermsList()
            for f in f_t_s:
                vals.append({
                    f["id"]:{
                        "value": [f["id"]],
                        "summary": f'{f["id"]}: {f['label']}'
                    }
                })

        return vals


################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    api()
