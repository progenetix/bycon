#!/usr/local/bin/python3

from os import path, pardir, system
from bycon import *

dir_path = path.dirname( path.relpath(__file__) )
project_path = path.join( dir_path, pardir )

"""
This script uses the `datatable_definitions.yaml` from `bycon` tpo generate import
tables for the different entities (and a general `metadata_template.tsv` for all
non-variant parameters) in the local `rsrc/templates/` directory.
"""

################################################################################

def main():
    dt_m = BYC["datatable_mappings"].get("$defs", {})
    ordered_mcs = BYC["datatable_mappings"].get("ordered_metadata_core", [])
    ordered_vcs = BYC["datatable_mappings"].get("ordered_variants_core", [])
    rsrc_p = path.join(project_path, "rsrc", "templates")
    root_path = input(f'Templates will be saved inside\n=> {rsrc_p}\nEnter a different path or just hit ENTER to use the default:\n')

    if len(root_path) > 0:
        if path.exists(root_path):
            rsrc_p = root_path
        else:
            print(f'Path\n{root_path}\ndoes not exist; using default path\n=> {rsrc_p}')

    s_no = 0
    proceed = input(f'Do you want to create individual_id & biosample_id & analysis_id values?\nEnter a number or just hit ENTER for no id values: ')
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
            "biosample_id": f'{pre}bs-{rid}',
            "analysis_id": f'{pre}cs-{rid}',
            "individual_id": f'{pre}ind-{rid}'
        })

    all_cols = []

    for t_t, t_d in dt_m.items():
        if "genomicVariant" in t_t:
            continue
        entity_cols = []
        table = []
        for p_n, p_d in t_d["parameters"].items():
            p_t = p_d.get("type", "string")
            entity_cols.append(p_n)
            if not "variant" in t_t.lower() and not p_n in all_cols:
                all_cols.append(p_n)

        f_n = t_t.replace("analysis", "analyse")+"s.tsv"
        f_p = path.join(rsrc_p, f_n)
        f = open(f_p, "w")
        f.write("{}\n".format("\t".join(entity_cols)))
        if "variant" in t_t.lower():
            f.close()
            print(f'===> Wrote {f_p}')
            continue
        for id_s in ids:
            d_line = []
            for p_n in entity_cols:
                d_line.append(id_s.get(p_n, ""))
            f.write("{}\n".format("\t".join(d_line)))
        f.close()
        print(f'===> Wrote {f_p}')

    # (semi-)ordered headers for the "metadata from all entities" files
    o_c_s = []
    a_c_s = []
    for c in ordered_mcs:
        if c in all_cols:
            o_c_s.append(c)
            a_c_s.append(c)
    for c in all_cols:
        if c not in a_c_s:
            a_c_s.append(c)

    a_p = path.join(rsrc_p, "metadata_all.tsv")
    c_p = path.join(rsrc_p, "metadata.tsv")
    f = open(a_p, "w")
    f.write("{}\n".format("\t".join(a_c_s)))
    for id_s in ids:
        d_line = []
        for p_n in a_c_s:
            d_line.append(id_s.get(p_n, ""))
        f.write("{}\n".format("\t".join(d_line)))
    f.close()  
    print(f'===> Wrote {a_p}')
    f = open(c_p, "w")
    f.write("{}\n".format("\t".join(a_c_s)))
    for id_s in ids:
        d_line = []
        for p_n in o_c_s:
            d_line.append(id_s.get(p_n, ""))
        f.write("{}\n".format("\t".join(d_line)))
    f.close()  
    print(f'===> Wrote {c_p}')


    # genomicVariant
    a_v_s = dt_m["genomicVariant"]["parameters"].keys()
    a_v_p = path.join(rsrc_p, "variants_all.tsv")
    c_v_p = path.join(rsrc_p, "variants.tsv")
    f = open(a_v_p, "w")
    f.write("{}\n".format("\t".join(a_v_s)))
    f.close()  
    print(f'===> Wrote {a_v_p}')
    f = open(c_v_p, "w")
    f.write("{}\n".format("\t".join(ordered_vcs)))
    f.close()  
    print(f'===> Wrote {c_v_p}')

    system(f'open {rsrc_p}')

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
