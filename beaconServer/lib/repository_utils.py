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

def geosoft_preclean_sample_characteristics(gsm_soft, byc):

    s_c_f = []

    s_c = list(filter(lambda x:'Sample_characteristics' in x, gsm_soft))

    for l in s_c:

        for p in byc["remap_definitions"]["line_patterns"]["cleanup"]:
            l = re.sub(r'{0}'.format(p["m"]), p["s"], l)
            
        # since matches require some length (label ...)
        if len(l) > 1:
            s_c_f.append(l)

    return s_c_f

##############################################################################     

def geosoft_extract_tumor_stage(s_c, collector, scope, byc):

    update_key = "pathological_stage"

    s_c = list(filter(lambda x:'stage' in x.lower(), s_c))

    for l in s_c:
        for p in byc["remap_definitions"]["line_patterns"][update_key]:
            if re.match(r'{0}'.format(p), l, re.IGNORECASE):

                stage = re.match(r'{0}'.format(p), l, re.IGNORECASE).group(1)
                stage = re.sub("4", "IV", stage)
                stage = re.sub("3", "III", stage)
                stage = re.sub("2", "II", stage)
                stage = re.sub("1", "IV", stage)
                stage = re.sub("S", "s", stage)

                collector.update({ scope["t_head"]: stage, "_input_stage": l })
                return collector

        # Fallback in case of no match for some feedback
        collector.update({ "_input_stage": l, "_note_stage": "no stage match" })

    return collector

##############################################################################

def geosoft_extract_tumor_grade(s_c, collector, scope, byc):

    update_key = "tumor_grade"

    s_c = list(filter(lambda x:'grade' in x.lower(), s_c))

    for l in s_c:
        for p in byc["remap_definitions"]["line_patterns"][update_key]:
            if re.match(r'{0}'.format(p), l, re.IGNORECASE):

                grade = re.match(r'{0}'.format(p), l, re.IGNORECASE).group(1)
                grade = re.sub("G", "", grade)
                grade = re.sub("III", "3", grade)
                grade = re.sub("II", "2", grade)
                grade = re.sub("IV", "4", grade)
                grade = re.sub("I", "1", grade)

                collector.update({ scope["t_head"]: grade, "_input_grade": l })
                return collector

        collector.update({ "_input_stage": l, "_note_stage": "no stage match" })
                
    return collector

##############################################################################

def geosoft_extract_gpl(gsm_soft, platform_re):

    gpl = ""
    s_c = list(filter(lambda x:'GPL' in x, gsm_soft))
    for l in s_c:
        if platform_re.match(l):
            gpl = platform_re.match(l).group(1)
            return gpl
                
    return gpl

##############################################################################

def geosoft_extract_gse(gsm_soft, series_re):

    gse = ""
    s_c = list(filter(lambda x:'GSE' in x, gsm_soft))
    for l in s_c:
        if series_re.match(l):
            gse = series_re.match(l).group(1)
            return gse
                
    return gse

##############################################################################

def geosoft_retrieve_tumor_stage(gsm, gsm_soft, update_obj, byc, counts):

    s_c = list(filter(lambda x:'Sample_characteristics' in x, gsm_soft))

    update_key = "pathological_stage"

    matched = False

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

        for p in byc["remap_definitions"]["line_patterns"][update_key]:

            if re.match(r'{0}'.format(p), l, re.IGNORECASE):

                stage = re.match(r'{0}'.format(p), l, re.IGNORECASE).group(1)
                stage = re.sub("4", "IV", stage)
                stage = re.sub("3", "III", stage)
                stage = re.sub("2", "II", stage)
                stage = re.sub("1", "IV", stage)

                if not "tumor_stage" in update_obj["info"]:
                    print("\n!!!! {}: found new stage {}".format(gsm, stage))
                    counts["new_stages"] += 1
                
                t_s = remap_from_pattern(update_key, stage, byc)
                # Data is only updated if there was a correct pattern
                if t_s:
                    update_obj["info"].update({"tumor_stage":stage})
                    update_obj.update({ update_key: t_s })
                    matched = True
                    continue

        if not matched:
            print("no stage regex match {}".format(l))

    return update_obj, counts, matched


##############################################################################

def geosoft_retrieve_tumor_grade(gsm, gsm_soft, update_obj, byc, counts):

    s_c = list(filter(lambda x:'Sample_characteristics' in x, gsm_soft))

    update_key = "tumor_grade"

    matched = False

    for l in s_c:

        if not "grade" in l.lower():
            continue

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
                
                t_s = remap_from_pattern(update_key, grade, byc)
                # Data is only updated if there was a correct pattern

                update_obj["info"].update({"tumor_grade":grade})

                matched = True

                if t_s:
                    update_obj["info"].update({"tumor_grade":grade})
                    update_obj.update({ update_key: t_s })
                    matched = True
                    continue

        if not matched:
            print("\nno grade regex match {}".format(l))
        else:
            continue

    return update_obj, counts, matched


