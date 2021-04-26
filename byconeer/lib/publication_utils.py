#!/usr/bin/env python3

import requests
import json, re
import csv
from os import path

##############################################################################

def jprint(obj):
    text = json.dumps(obj, sort_keys= True, indent = 4, ensure_ascii = False)
    print(text)

##############################################################################

def read_annotation_table(args):

    f_p = args.filepath

    if not args.filepath:
        print("!!! No file provided using `-f` !!!")
        exit()

    if not path.isfile( args.filepath ):
        print("!!! No file at {} !!!".format(args.filepath))
        exit()

    l = [] 
    with open(f_p) as f:
       rd = csv.reader(f, delimiter="\t", quotechar='"')
       for i, row in enumerate(rd):
           if i > 0:
               l.append(row)

    return l

##############################################################################

def retrieve_epmc_publications(pmid):
    
    parameters = {
        "query": "ext_id:" + pmid,
        "format": "json",
        "resultType": "core"
        }
    response = requests.get("https://www.ebi.ac.uk/europepmc/webservices/rest/search", params = parameters)
    
    if response.status_code == 200:
        results = response.json()["resultList"]["result"]
        informations = results[0]
            
    return informations if (informations["pmid"] == pmid) else print(f"Warning: PMID of the retrieved publication doesn't match with the query (PMID:{pmid})")
    
##############################################################################
 
def create_short_publication_label(author, title, year):
    
    short_author = re.sub(r'(.{2,32}[\w\.\-]+? \w\-?\w?\w?)(\,| and ).*?$', r'\1 et al.', author)

    if len(title) <= 100:
        label = short_author + f' ({year}) ' + title
    else:
        label = short_author + f' ({year}) ' + ' '.join(title.split(' ')[:12]) + ' ...'
        
    return label

##############################################################################

def get_geolocation(city, locationID): #heidelberg, heidelberg::germany

    where = {"city": city} 
    location = requests.get("https://progenetix.org/services/geolocations", params = where)
    coordinates = location.json()["response"]["results"]

    for info in coordinates:
        if info["id"] == locationID:
            del(info["id"])
            provenance = info
          
    return provenance

##############################################################################

def get_ncit_tumor_type(tumors, fullNames):
    
    # Convert "tumor" in a list containing [[ncit, counts], [ncit, counts], ...]
    types = tumors.split('; ') # if >1 tumor type is present, information must be separated by "; " (see test.txt)
    list_types = []
    for t in types:
        typ = t.split(', ')
        list_types.append(typ)
    
    # Convert fullNames string into a list
    names = fullNames.split('; ')

    # Fill in sample_types list
    sample_types = []
    for i, typ in enumerate(list_types):
        tumor_type = {}
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

def create_progenetix_posts(rows):

    posts = []
    
    for row in rows:
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
                        "provenance": get_geolocation(row[8], row[9]),
                        "sample_types": get_ncit_tumor_type(row[11], row[12]), 
                        "sortid": None, 
                        "title": title,
                        "year": year
                        })  
            
            pub_copy = pub.copy()
            posts.append(pub_copy)
        
    return posts

