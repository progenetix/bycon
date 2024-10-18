#!/usr/bin/env python3

import inspect, sys, re, yaml
from os import getlogin, makedirs, path, system
from pathlib import Path

dir_path = path.dirname( path.abspath(__file__) )

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

        pp_fh.write(f'## `{fn}`\n\n')

        func = getattr(byconServices, fn)
        pp_fh.write(f'{inspect.getdoc(func)}\n\n\n')

    pp_fh.close()


################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
