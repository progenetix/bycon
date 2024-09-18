import re
from progress.bar import Bar

from config import BYC, BYC_PARS

################################################################################

def set_collation_types():
    f_d_s = BYC.get("filter_definitions", {})
    cts = BYC_PARS.get("collation_types")
    if not cts:
        return
    s_p = {}
    for p in cts:
        if not (p_d := f_d_s.get(p)):
            continue
        if p_d.get("collationed", True) is False:
            continue
        s_p.update({p: p_d})
    if len(s_p.keys()) < 1:
        print("No existing collation type was provided with `--collationTypes` ...")
        exit()
    BYC.update({"filter_definitions":s_p})

    return


################################################################################

def hierarchy_from_file(ds_id, coll_type, pre_h_f):
    f_d_s = BYC.get("filter_definitions", {})
    coll_defs = f_d_s[coll_type]
    hier = { }
    f = open(pre_h_f, 'r+')
    h_in  = [line for line in f.readlines()]
    f.close()
    parents = [ ]
    no = len(h_in)
    bar = Bar(coll_type, max = no, suffix='%(percent)d%%'+" of "+str(no) )
    for c_l in h_in:
        bar.next()
        c, l, d, i = re.split("\t", c_l.rstrip() )
        d = int(d)
        max_p = len(parents) - 1
        if max_p < d:
            parents.append(c)
        else:
            # if recursing to a lower column/hierarchy level, all deeper "parent" 
            # values are discarded
            parents[ d ] = c
            while max_p > d:
                parents.pop()
                max_p -= 1
        l_p = { "order": i, "depth": d, "path": parents.copy() }
        if not c in hier.keys():
            hier.update( { c: { "id": c, "label": l, "hierarchy_paths": [ l_p ] } } )
        else:
            hier[ c ]["hierarchy_paths"].append( l_p )
    bar.finish()

    return hier
