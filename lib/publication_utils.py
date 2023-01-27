import requests
import json, re, datetime
import csv
from pymongo import MongoClient
from os import path, pardir
from isodate import date_isoformat

from schema_parsing import *

##############################################################################

def jprint(obj):

    print(json.dumps(obj, indent=2, sort_keys=True, default=str))

##############################################################################

def retrieve_epmc_publications(pmid):

    pub_info = {}
    e = False

    pmid = re.sub(" ", "", pmid)
    
    parameters = {
        "query": "ext_id:" + pmid,
        "format": "json",
        "resultType": "core"
    }

    response = requests.get("https://www.ebi.ac.uk/europepmc/webservices/rest/search", params = parameters)
    if response.status_code == 200:
        results = response.json()["resultList"]["result"]
        if len(results) > 0:
            pub_info = results[0]

    if pub_info.get("pmid", "___none___") != pmid:
        e = f"¡¡¡ Skipping {pmid}: PMID of the retrieved entry doesn't match (possibly EPMC delay?)"
            
    return pub_info, e
    
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

def publication_update_label(publication):
    
    short_author = re.sub(r'(.{2,32}[\w\.\-]+? \w\-?\w?\w?)(\,| and ).*?$', r'\1 et al.', publication["authors"])

    if len(publication["title"]) <= 80:
        publication.update({"label": short_author + f' ({publication["pub_year"]}) ' + publication["title"]})
    else:
        publication.update({"label": short_author + f' ({publication["pub_year"]}) ' + ' '.join(publication['title'].split(' ')[:12]) + ' ...' })
        
    return publication


##############################################################################

def get_ncit_tumor_types(n_p, pub):

    try:
        if not "::" in pub["SAMPLE_TYPES"]:
            return n_p
    except KeyError:
        return n_p

    s_t_s = pub["SAMPLE_TYPES"].split(';')

    s_t_l = []

    for s_t in s_t_s:

        # print(s_t)
      
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
    # e_p_s = read_schema_file("Publication", "properties", byc)
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
