#!/usr/bin/env python3

import inspect, sys, re, yaml
from os import getlogin, makedirs, path, system
from pathlib import Path

dir_path = path.dirname( path.abspath(__file__) )

from bycon import BYC
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

    pp_f = path.join(generated_docs_path, f"services.md")
    pp_fh = open(pp_f, "w")
    md = []
    for f in sorted(s_p_s):
        fn = f.name.split('.')[0]
        if fn in [ "__init__"]:
            continue
        # print(f'from {fn} import {fn}')

        pp_fh.write(f'## `/{fn}`\n\n')

        func = getattr(byconServices, fn)
        pp_fh.write(f'{inspect.getdoc(func)}\n\n\n')

    pp_fh.close()

    #>------------------------------------------------------------------------<#


    pp_f = path.join(generated_docs_path, f"beacon-responses.md")
    pp_fh = open(pp_f, "w")
    md = []
    beacon_ets = {}
    pp_fh.write("""# Beacon Responses

The following is a list of standard Beacon responses supported by the `bycon` package.
Responses for individual entities or endpoints are grouped by their Beacon framework
response classes (e.g. `beaconResultsetsResponse` for `biosamples`, `g_variants` etc.).

Please be reminded about the general syntax used in Beacon: A **path element** such
as `/biosamples` corresponds to an entity (here `biosample`). Below these relations
are indicated by the `@` symbol.
\n\n""")

    for e, e_d in BYC["entity_defaults"].items():
        if not (e_d.get("is_beacon_entity", False)):
            continue
        r_s = e_d.get("response_schema")
        if not r_s in beacon_ets:
            beacon_ets.update({r_s: []})
        beacon_ets[r_s].append(e_d)

    for r_s in beacon_ets:
        pp_fh.write(f'## {r_s}\n\n')
        for e_d in beacon_ets[r_s]:
            pp_fh.write(f'### {e_d["response_entity_id"]} @ `/{e_d["request_entity_path_id"]}`\n\n')
            if (d := e_d.get("description")):
                pp_fh.write(f'#### Description\n\n{e_d["description"]}\n\n')
            if (s := e_d.get("beacon_schema")):
                pp_fh.write(f'#### Schema for _{s.get("entity_type")}_\n\n')
                pp_fh.write(f'* <{s.get("schema", "")}>\n\n')
            test_url = '{{config.reference_server_url}}/beacon' + f'/{e_d["request_entity_path_id"]}'
            if "BeaconDataResponse" in e_d.get("bycon_response_class", ""):
                test_url += "?testMode=true"
            pp_fh.write(f'#### Tests\n\n* <{test_url}>\n\n')
            for e in e_d.get("tests", []):
                e_url = '{{config.reference_server_url}}/beacon' + f'/{e_d["request_entity_path_id"]}'
                pp_fh.write(f'* <{e_url}{e}>\n\n')
            pp_fh.write('\n\n')
    pp_fh.close()


    #>------------------------------------------------------------------------<#

    file_pars = {
        "plot_defaults":{
            "chapters": {
                "plot_type_defs": "Plot Types",
                "plot_parameters": "Plot Parameters"
            },
            "title": "Plot Parameters and Information"
        },
        "argument_definitions": {
            "title": "`bycon` Arguments and Parameters",
            "preamble": "The following is a list of arguments and parameters used in the `bycon` package as well as the `byconaut` tools."
        }
    }

    for d_k, d_v in file_pars.items():
        if d_k not in BYC:
            continue

        pp_f = path.join(generated_docs_path, f"{d_k}.md")

        ls = [f'# {d_v.get("title")}']
        ls.append(f'{d_v.get("preamble", "")}')

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
            ls.append(f'## {title}')
            for pk, pi in pp.items():
                ls.append(f'### `{pk}` \n')

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
