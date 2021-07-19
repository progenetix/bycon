#!/usr/bin/env python3

import requests
import json, re
import csv
from pymongo import MongoClient
from os import path, pardir
from humps import decamelize

# local
lib_path = path.dirname( path.abspath(__file__) )
dir_path = path.join( lib_path, pardir )
pkg_path = path.join( dir_path, pardir )

##############################################################################

def jprint(obj):
    text = json.dumps(obj, sort_keys= True, indent = 4, ensure_ascii = False)
    print(text)

##############################################################################

def read_annotation_table(byc):

    if not byc["args"].filepath:
        print("!!! No file provided using `-f` !!!")
        exit()

    if not path.isfile( byc["args"].filepath ):
        print("!!! No file at {} !!!".format(byc["args"].filepath))
        exit()

    l = [] 
    with open(byc["args"].filepath) as f:
       rd = csv.reader(f, delimiter="\t", quotechar='"')
       for i, row in enumerate(rd):
           if i > 0:
               l.append(row)

    return l

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

def get_geolocation(locationID, byc):

    #heidelberg, heidelberg::germany

    # TODO: Use schema file & parser for empty instance.
    provenance = {
        "type" : "Feature",
        "geometry" : {
            "type" : "Point",
            "coordinates" : [
                0,
                0
            ]
        },
        "properties" : {
            "ISO3166alpha2" : "XX",
            "ISO3166alpha3" : "XXX",
            "city" : "Atlantis",
            "continent" : "Null Island",
            "country" : "Null Island"
        }
    }

    locationID = re.sub(" ", "", locationID)

    mongo_client = MongoClient()
    geo_info = mongo_client["progenetix"]["geolocs"].find_one({"id": locationID})
    if not geo_info:
        print("!!! no geo match for {}".format(locationID))
        return provenance

    return geo_info["geo_location"]

##############################################################################

def get_ncit_tumor_type(tumors, fullNames):
    
    # Convert "tumor" in a list containing [[ncit, counts], [ncit, counts], ...]
    tumors = re.sub(" ", "", tumors)
    types = ';'.split(tumors) # if >1 tumor type is present, information must be separated by ";" (see test.txt)
    list_types = []
    for t in types:
        typ = t.split(',')
        list_types.append(typ)
    
    # Convert fullNames string into a list
    fullNames = re.sub("; ", ";", fullNames)
    names = fullNames.split(';')

    # Fill in sample_types list
    sample_types = []
    for i, typ in enumerate(list_types):
        if "C" in typ:
            tumor_type = {}
            print(typ)
            ID = "NCIT:" + typ[0]
            counts = int(typ[1])
            tumor_type.update({"id": ID,
                               "label": names[i],
                               "counts": counts,
                               })
            
            tumor_copy = tumor_type.copy()
            sample_types.append(tumor_copy)
        
    return sample_types

##############################################################################

def create_progenetix_post(row, byc):

    pub_copy = False

    pub = {}
    info = retrieve_epmc_publications(row[0]) 
    if info != None: ### only if publication PMID matched the query
        abstract = info["abstractText"]
        ID = info["pmid"]
        author = info["authorString"]
        journal = info["journalInfo"]["journal"]["medlineAbbreviation"]
        title = info["title"]
        year = info["pubYear"]
        
        # Remove HTML formatting:
        abstract_no_html = re.sub(r'<[^\>]+?>', "", abstract)
        title_no_html = re.sub(r'<[^\>]+?>', "", title)
        abstract, title = abstract_no_html, title_no_html
        
        # Fill in counts:
        counts = {}
        counts.update({"acgh": int(row[1]),
                        "arraymap": 0,
                        "ccgh": int(row[2]),
                        "genomes": int(row[3]),
                        "ngs": int(row[4]),
                        "progenetix": int(row[5]),
                        "wes": int(row[6]),
                        "wgs": int(row[7])
                         })
           
        pub.update({"abstract": abstract,
                    "authors": author,
                    "counts": counts,
                    "id": "PMID:" + str(ID),
                    "label": create_short_publication_label(author, title, year), 
                    "journal": journal,
                    "provenance": {"geo_location":get_geolocation(row[9], byc) },
                    "sample_types": get_ncit_tumor_type(row[11], row[12]), 
                    "sortid": None, 
                    "title": title,
                    "year": year
                    })  
        
        pub_copy = pub.copy()
        
    return pub_copy

