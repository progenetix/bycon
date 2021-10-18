#!/usr/bin/env python3

import requests
import json, re, datetime
import csv
from pymongo import MongoClient
from os import path, pardir
from humps import decamelize
from isodate import date_isoformat

from schemas_parser import *

##############################################################################

def jprint(obj):

    print(json.dumps(obj, indent=2, sort_keys=True, default=str))

##############################################################################

def retrieve_epmc_publications(pmid):

    informations = { "pmid" : "" } # dirty, to avoind another test
    
    parameters = {
        "query": "ext_id:" + pmid,
        "format": "json",
        "resultType": "core"
    }

    response = requests.get("https://www.ebi.ac.uk/europepmc/webservices/rest/search", params = parameters)
    
    if response.status_code == 200:
        results = response.json()["resultList"]["result"]
        if len(results) > 0:
            informations = results[0]
            
    return informations if (informations["pmid"] == pmid) else print(f"Warning: PMID of the retrieved publication doesn't match with the query (PMID:{pmid})")
    
##############################################################################

def update_from_epmc_publication(publication, epmc):

    if epmc is None:
        return publication

    publication.update({"abstract": re.sub(r'<[^\>]+?>', "", epmc.get("abstractText", "") ) } )
    publication.update({"authors": epmc.get("authorString", "") })
    publication.update({"journal": epmc["journalInfo"]["journal"]["medlineAbbreviation"]})
    publication.update({"title":re.sub(r'<[^\>]+?>', "", epmc.get("title", "") ) })
    publication.update({"pub_year": epmc.get("pubYear", "") } )
    publication.update({"pmcid": epmc.get("pmcid", "") })

    return publication

##############################################################################

def create_short_publication_label(publication):
    
    short_author = re.sub(r'(.{2,32}[\w\.\-]+? \w\-?\w?\w?)(\,| and ).*?$', r'\1 et al.', publication["authors"])

    if len(publication["title"]) <= 80:
        publication.update({"label": short_author + f' ({publication["pub_year"]}) ' + publication["title"]})
    else:
        publication.update({"label": short_author + f' ({publication["pub_year"]}) ' + ' '.join(publication['title'].split(' ')[:12]) + ' ...' })
        
    return publication


##############################################################################

def get_ncit_tumor_types(n_p, pub):

    try:
        if not "::" in pub["#sample_types"]:
            return n_p
    except KeyError:
        return n_p

    s_t_s = pub["#sample_types"].split(';')

    s_t_l = []

    for s_t in s_t_s:
      
        c, l, n = s_t.split('::')

        if c.startswith("C"):
            c = "NCIT:"+c

        s_t_l.append({
          "id": c,
          "label": l,
          "count": int(n)
        })

    n_p.update({"sample_types": s_t_l})
         
    return n_p

##############################################################################

def get_empty_publication(byc):

    pub_p = path.join( pkg_path, "schemas", "ProgenetixLinkML", "Publication.json#/$defs/Publication/properties")

    root_def = RefDict(pub_p)
    exclude_keys = [ "format", "examples", "_id" ]
    e_p_s = materialize(root_def, exclude_keys = exclude_keys)
    # e_p_s = read_schema_files("Publication", "properties", byc)
    p = create_empty_instance(e_p_s)
    _assign_publication_defaults(p)
    
    return p

##############################################################################

def _assign_publication_defaults(publication):

    publication.update({
        "updated": date_isoformat(datetime.datetime.now()),
        "provenance": {
            "geo_location": {
              "type": 'Feature',
              "geometry": { "type": 'Point', "coordinates": [ 0, 0 ] },
              "properties": {
                "label": 'Atlantis, Null Island',
                "city": 'Atlantis',
                "country": 'Null Island',
                "continent": 'Africa',
                "latitude": 0,
                "longitude": 0,
                "ISO3166alpha3": 'AAA',
                "precision": 'city'
              }
            }
        },
        "counts": { "ccgh": 0, "acgh": 0, "wes": 0, "wgs": 0, "ngs": 0, "genomes": 0, "progenetix": 0, "arraymap": 0 },
        })

    return publication

##############################################################################
