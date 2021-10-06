#!/usr/bin/env python3

import requests
import json, re, datetime
import csv
from pymongo import MongoClient
from os import path, pardir
from humps import decamelize
from isodate import date_isoformat


# local
lib_path = path.dirname( path.abspath(__file__) )
dir_path = path.join( lib_path, pardir )
pkg_path = path.join( dir_path, pardir )

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
 
def create_short_publication_label(author, title, year):
    
    short_author = re.sub(r'(.{2,32}[\w\.\-]+? \w\-?\w?\w?)(\,| and ).*?$', r'\1 et al.', author)

    if len(title) <= 80:
        label = short_author + f' ({year}) ' + title
    else:
        label = short_author + f' ({year}) ' + ' '.join(title.split(' ')[:12]) + ' ...'
        
    return label


##############################################################################

def get_ncit_tumor_types(n_p, pub):

    s_t_s = pub["_sample_types"].split(';')

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

def get_empty_publication():
    return {
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
        "counts": { "ccgh": 0, "acgh": 0, "wes": 0, "wgs": 0, "ngs": 0, "genomes": 0, "progenetix": 0},
        "id": '',
        "abstract": '',
        "contact": {
            "affiliation": '',
            "email": '',
            "name": '',
        },
        "authors": '',
        "journal": '',
        "note": '',
        "status": '',
        "title": '',
        "year": '',
        "pubmedid": '',
        "info": {},
        "label": '',
        "sample_types": [],
        "progenetix_curator": ''
    }


