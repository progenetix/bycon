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

        for p in byc["text_patterns"]["line_cleanup"]["cleanup"]:
            l = re.sub(r'{0}'.format(p["m"]), p["s"], l)
            
        # since matches require some length (label ...)
        if len(l) > 1:
            s_c_f.append(l)

    return s_c_f

##############################################################################     

def geosoft_extract_geo_meta(s_c, collector, scope, byc):

    patterns = byc["text_patterns"]["extraction_scopes"][ scope["ontologized_parameter"] ]

    s_c = list(filter(lambda x:re.match(r'{0}'.format(patterns["filter"]), x), s_c))

    for l in s_c:
        o_l = l
        if "preclean" in patterns:
            for p in patterns["preclean"]:
                l = re.sub(r'{0}'.format(p["m"]), p["s"], l)
        if len(l) < 2:
            print(o_l)
            continue

        for p in patterns["find"]:
            if re.match(r'{0}'.format(p), l):
                m = re.match(r'{0}'.format(p), l).group(1)
                for c in patterns["cleanup"]:
                    m = re.sub(r'{0}'.format(c["m"]), c["s"], m)

                if not re.match(r'{0}'.format(patterns["final_check"]), m):
                    continue

                collector.update({ scope["db_key"]: m, scope["text_input"]: l })
                return collector

        # Fallback in case of no match for some feedback
        collector.update({ scope["text_input"]: o_l, scope["error"]: "no "+scope["id"]+" match" })

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


