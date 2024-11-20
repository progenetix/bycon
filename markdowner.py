#!/usr/bin/env python3

import inspect, sys, re, yaml
from os import getlogin, makedirs, path, system
from pathlib import Path
from json_ref_dict import RefDict, materialize

dir_path = path.dirname( path.abspath(__file__) )

from bycon import * #BYC, read_schema_file
import byconServices

################################################################################

def main():
    """
    The `markdowner` script processes some of the inline documentation in the
    `bycon` package as well as some configuration files and generates markdown
    files for processing by the `mkdocs` website generator. It is invoked when
    running the local `./updev.sh` command.
    """
    generated_docs_path = path.join( dir_path, "docs", "generated")

    p = Path(path.join( dir_path, "byconServices" ))
    s_p_s = [ f for f in p.rglob("*.py") if f.is_file() ]

    pp_f = path.join(generated_docs_path, f"beacon-services.md")
    pp_fh = open(pp_f, "w")
    md = []
    for f in sorted(s_p_s):
        fn = f.name.split('.')[0]
        if fn in [ "__init__"]:
            continue
        # print(f'from {fn} import {fn}')

        pp_fh.write(f'### `/{fn}`\n\n')

        func = getattr(byconServices, fn)
        pp_fh.write(f'{inspect.getdoc(func)}\n\n\n')

    pp_fh.close()

    #>------------------------------------------------------------------------<#

    """
    The block below parses the `entity_defaults.yaml` file and extracts some
    definitions, examples and links for creating a Markdown page (for processing
    with the mkdocs engine).
    Very scripty single use code...
    """

    pp_f = path.join(generated_docs_path, f"beacon-responses.md")
    pp_fh = open(pp_f, "w")
    md = []
    # populating with the response types to enforce some order
    # and to add the non-document response types

    s_path = Path(path.join( PKG_PATH, "schemas", "framework", "src", "responses"))
    r_s_f = [ Path(f.name).stem for f in s_path.glob("beacon*") if f.is_file() ]

    beacon_ets = {}
    for r_s in r_s_f:
        beacon_ets.update({r_s: {"endpoints": []}})

    for e in ["beaconBooleanResponse", "beaconCountResponse"]:
        if e not in beacon_ets:
            continue
        beacon_ets[e].update({
        "postscript": """
For a list of entities potentially served by `beaconBooleanResponse` depending on
the selected or granted `responseGranularity` please check `beaconResultsetsResponse`.
"""
        })

    for e, e_d in BYC["entity_defaults"].items():
        if not (e_d.get("is_beacon_entity", False)):
            continue
        r_s = e_d.get("response_schema")
        if not r_s in beacon_ets:
            beacon_ets.update({r_s: {"endpoints": []}})
        beacon_ets[r_s]["endpoints"].append(e_d)

    for r_s in beacon_ets:
        pp_fh.write(f'## {r_s}\n\n')
        if (schema := read_schema_file(r_s, "")):
            if len((s_desc := schema.get("description"), "")) > 1:
                pp_fh.write(f'{s_desc}\n\n')
        e_url = '{{config.reference_server_url}}/services/schemas' + f'/{r_s}'
        pp_fh.write(f'* **{{S}}** <{e_url}>\n\n')
        for e_d in beacon_ets[r_s].get("endpoints", []):
            pp_fh.write(f'### {e_d["response_entity_id"]} @ `/{e_d["request_entity_path_id"]}`\n\n')
            b_s = e_d.get("beacon_schema", {})
            b_s_s = b_s.get("schema", "")
            b_s_n = b_s_s.rstrip("/").split('/')[-1]

            description = ""
            # TODO: Doesn't work if schema has reference to external file ...
            if (schema := read_schema_file(b_s_n, "")):
                if len((s_desc := schema.get("description"), "")) > 1:
                    description += f'{s_desc}\n\n'
            if (d := e_d.get("description")):
                description += f'{d}\n\n'
            if len(description) > 2:
                pp_fh.write(f'{description}\n\n')
            s_url = '{{config.reference_server_url}}/services/schemas' + f'/{b_s_n}'
            pp_fh.write(f'* **{{S}}** <{s_url}>\n\n')
            test_url = '{{config.reference_server_url}}/beacon' + f'/{e_d["request_entity_path_id"]}'
            if "BeaconDataResponse" in e_d.get("bycon_response_class", ""):
                test_url += "?testMode=true"
            pp_fh.write(f'* **{{T}}** <{test_url}>\n\n')
            if len(e_s := e_d.get("examples", [])) > 0:
                for e in e_s:
                    e_url = '{{config.reference_server_url}}/beacon' + f'/{e_d["request_entity_path_id"]}'
                    pp_fh.write(f'* **{{E}}** <{e_url}{e}>\n\n')
            pp_fh.write('\n\n')
        pp_fh.write(f'{beacon_ets[r_s].get("postscript", "")}\n\n')
    pp_fh.close()


    #>------------------------------------------------------------------------<#

    file_pars = {
        "plot_defaults":{
            "chapters": {
                "plot_type_defs": "Plot Types",
                "plot_parameters": "Plot Parameters"
            },
        },
        "argument_definitions": {}
    }

    for d_k, d_v in file_pars.items():
        if d_k not in BYC:
            continue

        pp_f = path.join(generated_docs_path, f"{d_k}.md")

        ls = []

        if not "chapters" in d_v:
            d_v = {
                "chapters":{
                    "root": "Definitions"}
            }

        for chapter, title in d_v.get("chapters").items():
            if "root" in chapter:
                pp = BYC[d_k]
            else:
                pp = BYC[d_k].get(chapter, {})
            ls.append(f'### {title}')
            for pk, pi in pp.items():
                ls.append(f'#### `{pk}` \n')

                for pik, piv in pi.items():
                    if type(piv) is dict:
                        js = '  \n'
                        ls.append(f'**{pik}:**  \n')
                        ls.append(js.join([f'    - `{k}`: `{v}`    ' for k, v in piv.items()]))                    
                    elif type(piv) is list:
                            js = ','
                            piv = js.join([str(x) for x in piv])
                            ls.append(f'**{pik}:** `{piv}`    ')
                    elif "default" in pik or "pattern" in pik and len(str(piv)) > 0:
                        ls.append(f'**{pik}:** `{piv}`    ')
                    elif "description" in pik:
                        ls.append(f'**{pik}:**\n')
                        piv = piv.replace("*", "    \n*")
                        ls.append(f'{piv}    ')
                    else:
                        ls.append(f'**{pik}:** {piv}    ')
                    ls.append(f'\n')
                ls.append(f'\n')

        pp_fh = open(pp_f, "w")
        pp_fh.write("\n".join(ls).replace("\n\n", "\n").replace("\n\n", "\n"))
        pp_fh.close()

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
