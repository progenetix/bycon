#!/usr/bin/env python3

import requests
import json, re, datetime
from os import path, pardir

from remap_utils import remap_from_pattern

##############################################################################

def read_geosoft_file(geo_acc, byc, filepath=False):

    geosoft = False

    acc_re = re.compile(r'^G[PS][EM]\d+?$')
    if not acc_re.match(geo_acc):
        return geosoft

    if filepath is False:
        geosoft = retrieve_geosoft_file(geo_acc, byc)
        return geosoft

##############################################################################

def retrieve_geosoft_file(geo_acc, byc):

    geosoft_url = "{}{}".format(byc["config"]["resource_urls"]["ncbi_geosoft"], geo_acc)

    # TODO: capture error
    r = requests.get(geosoft_url)
    geosoft = re.split("\n", r.text)
    return geosoft

##############################################################################

def geosoft_retrieve_tumor_stage(gsm, gsm_soft, update_obj, byc, counts):

    s_c = list(filter(lambda x:'Sample_characteristics' in x, gsm_soft))

    update_key = "pathological_stage"

    for l in s_c:

        if not "stage" in l.lower():
            continue

        """
        ## STAGE

        This is a test for some metadata extraction...
        This already requires "stage" to be mentioned on the line
        which may not always be the case. This avoids the expensive
        use of the regex patterns...
        """

        matched = False

        for p in byc["remap_definitions"]["line_patterns"][update_key]:

            if re.match(r'{0}'.format(p), l, re.IGNORECASE):

                stage = re.match(r'{0}'.format(p), l, re.IGNORECASE).group(1)
                stage = re.sub("4", "IV", stage)
                stage = re.sub("3", "III", stage)
                stage = re.sub("2", "II", stage)
                stage = re.sub("1", "IV", stage)

                if not "tumor_stage" in update_obj["info"]:
                    print("!!!! {}: found new stage {}".format(gsm, stage))
                    counts["new_stages"] += 1
                
                t_s = remap_from_pattern(update_key, stage, byc)
                # Data is only updated if there was a correct pattern
                if t_s:
                    update_obj["info"].update({"tumor_stage":stage})
                    update_obj.update({ update_key: t_s })
                    matched = True
                    continue

        if not matched:
            print("\nno stage regex match {}".format(l))

    return update_obj, counts


##############################################################################

def geosoft_retrieve_tumor_grade(gsm, gsm_soft, update_obj, byc, counts):

    s_c = list(filter(lambda x:'Sample_characteristics' in x, gsm_soft))

    update_key = "tumor_grade"

    for l in s_c:

        if not "grade" in l.lower():
            continue

        matched = False

        for p in byc["remap_definitions"]["line_patterns"][update_key]:

            if re.match(r'{0}'.format(p), l, re.IGNORECASE):

                grade = re.match(r'{0}'.format(p), l, re.IGNORECASE).group(1)
                grade = re.sub("G", "", grade)
                # grade = re.sub("3", "III", grade)
                # grade = re.sub("2", "II", grade)
                # grade = re.sub("1", "IV", grade)

                if not "tumor_grade" in update_obj["info"]:
                    print("!!!! {}: found new grade {}".format(gsm, grade))
                    counts["new_grades"] += 1
                
                # t_s = remap_from_pattern(update_key, grade, byc)
                # Data is only updated if there was a correct pattern

                update_obj["info"].update({"tumor_grade":grade})

                matched = True

                # if t_s:
                #     update_obj["info"].update({"tumor_grade":grade})
                #     update_obj.update({ update_key: t_s })
                #     matched = True
                #     continue

        if not matched:
            print("\nno grade regex match {}".format(l))

    return update_obj, counts


