#!/usr/bin/env python3

from os import path, pardir, system
from bycon import *
from byconServiceLibs import ByconID

dir_path = path.dirname( path.relpath(__file__) )
pkg_path = path.join( dir_path, pardir )

"""
This script uses the `datatable_definitions.yaml` from `bycon` tpo generate import
tables for the different entities (and a general `metadata_template.tsv` for all
non-variant parameters) in the local `rsrc/templates/` directory.
"""

################################################################################
################################################################################
################################################################################

def main():

    initialize_bycon_service()

    dt_m = BYC["datatable_mappings"].get("definitions", {})
    rsrc_p = path.join(pkg_path, "rsrc", "templates")
    s_no = 0
    proceed = input(f'Do you want to create individual_id & biosample_id & analysis_id values?\nEnter a number; hit ENTER for no id values: ')
    if re.match(r'^\d+?$', proceed):
        s_no = int(proceed)
            
    if s_no > 0:
        pre = "pgx"
        proceed = input(f'Do you want a prefix instead of "{pre}"?\nPrefix: ')
        if re.match(r'^\w+?$', proceed):
            pre = proceed

        tdir = f'{isotoday()}-{pre}'
        proceed = input(f'Do you want a specific directory name instead of "{tdir}"?\nDir name (no path, just directory...): ')
        if re.match(r'^\w+?$', proceed):
            tdir = proceed
        rsrc_p = path.join(rsrc_p, tdir)
        if not path.exists(rsrc_p):
            system(f'mkdir {rsrc_p}')

    ids = []
    BID = ByconID()
    for i in range(s_no):
        rid = BID.makeID()
        ids.append({
            "biosample_id": f'{pre}bios-{rid}',
            "analysis_id": f'{pre}ana-{rid}',
            "individual_id": f'{pre}ind-{rid}'
        })

    all_cols = []

    for t_t, t_d in dt_m.items():
        entity_cols = []
        table = []
        for p_n, p_d in t_d["parameters"].items():
            p_t = p_d.get("type", "string")
            entity_cols.append(p_n)
            if "variant" not in t_t.lower() and p_n not in all_cols:
                all_cols.append(p_n)

        table.append("\t".join(entity_cols))

        if "variant" not in t_t.lower():
            for id_s in ids:
                d_line = []
                for p_n in entity_cols:
                    t_v = ""
                    if p_n in id_s:
                        t_v = id_s.get(p_n)
                    d_line.append(t_v)
                table.append("\t".join(d_line))

        f_p = path.join(rsrc_p, t_t+"_template.tsv")
        f = open(f_p, "w")
        f.write("\n".join(table))
        f.close()
        print(f'===> Wrote {f_p}')

    f_p = path.join(rsrc_p, "metadata_template.tsv")
    f = open(f_p, "w")
    f.write("\t".join(all_cols)+"\n")
    f.close()
    print(f'===> Wrote {f_p}')
    system(f'open {rsrc_p}')

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
