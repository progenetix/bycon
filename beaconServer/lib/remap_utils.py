#!/usr/bin/env python3

import re

################################################################################

def remap_from_pattern(update_key, from_value, byc):

    if not update_key in byc["remap_definitions"]["ontology_remaps"].keys():
        return False

    if not isinstance(from_value, str):
        return False

    if len(from_value) < 1:
        return False

    r_d = byc["remap_definitions"]["ontology_remaps"][update_key]

    for c_p in r_d["class_patterns"]:
        if re.match(r'{0}'.format(c_p["pattern"]), from_value, re.IGNORECASE):
            return { "id": c_p["id"], "label": c_p["label"] }

################################################################################
