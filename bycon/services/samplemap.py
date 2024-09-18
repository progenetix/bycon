#!/usr/bin/env python3
import sys, traceback
from os import path
from pathlib import Path

from bycon import *

services_lib_path = path.join( path.dirname( path.abspath(__file__) ), "lib" )
sys.path.append( services_lib_path )
from geomap_utils import *

"""
"""

################################################################################
################################################################################
################################################################################

def main():
    try:
        samplemap()
    except Exception:
        print_text_response(traceback.format_exc(), 302)

################################################################################

def samplemap():
    initialize_bycon_service()
    BYC.update({"response_entity_id": "biosample"})
    BYC_PARS.update({"marker_type": "marker"})
    RSD = ByconResultSets().datasetsData()

    collated_results = []
    for ds_id, data in RSD.items():
        collated_results += data

    geob = __geo_bundle_from_results(collated_results)
    ByconMap(geob).printMapHTML()


################################################################################

def __geo_bundle_from_results(c_r):
    geokb = {}
    for r in c_r:
        try:
            geom = r["provenance"]["geo_location"]["geometry"]
            properties = r["provenance"]["geo_location"]["properties"]
        except:
            continue
        longlat = geom.get("coordinates", [0,0])
        k = f"longlat_{longlat[0]}_{longlat[1]}"
        if k not in geokb:
            geokb.update({k: {
                "pubmeds": {},
                "geo_location":
                {
                    "geometry": geom,
                    "properties": properties
                }
            }})
            geokb[k]["geo_location"]["properties"].update({"marker_count": 1})
        else:
            geokb[k]["geo_location"]["properties"]["marker_count"] += 1

        try:
            pmid = r["references"]["pubmed"]["id"]
            pmid = pmid.replace("PMID:", "")
            if pmid in geokb[k]["pubmeds"]:
                geokb[k]["pubmeds"][pmid]["count"] += 1
            else:
                lab = f"<a href='https://europepmc.org/article/MED/{pmid}' />{pmid}</a>"
                geokb[k]["pubmeds"].update({
                    pmid: {
                        "label": lab,
                        "count": 1
                    }
                })
        except:
            pass

    for k, v in geokb.items():
        m_c = v["geo_location"]["properties"].get("marker_count", 0)
        m_l = v["geo_location"]["properties"].get("label", "")
        v["geo_location"]["properties"].update({
            "label": f'{m_l} ({m_c} {"sample" if m_c == 1 else "samples"})',
            "items": []

        })
        for p_i in v["pubmeds"].values():
            l = p_i.get("label")
            c = p_i.get("count")
            if not l or not c:
                continue
            # v["geo_location"]["properties"]["items"].append('x')
            v["geo_location"]["properties"]["items"].append(f'{l} ({c} {"sample" if c == 1 else "samples"})')

    return list(geokb.values())


################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
