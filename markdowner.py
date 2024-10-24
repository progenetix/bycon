#!/usr/bin/env python3

import inspect, sys, re, yaml
from os import getlogin, makedirs, path, system
from pathlib import Path

dir_path = path.dirname( path.abspath(__file__) )

from bycon import BYC
import byconServices

################################################################################

def main():
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
