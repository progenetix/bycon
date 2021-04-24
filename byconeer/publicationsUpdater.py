#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 13 08:31:47 2021

@author: sofiapfund
"""

import requests
import json
import re
import csv
from pymongo import MongoClient
client = MongoClient() 
cl = client['progenetix'].publications

def jprint(obj):
    text = json.dumps(obj, sort_keys= True, indent = 4, ensure_ascii = False)
    print(text)

##############################################################################

def read_annotation_table(file_path):
    l = [] 
    with open(file_path) as f:
       rd = csv.reader(f, delimiter="\t", quotechar='"')
       for i, row in enumerate(rd):
           if i > 0:
               l.append(row)
    return l

path = "/Users/sofiapfund/Desktop/Internship/Scripts/retrieve_publications/publications.txt" ### path of your .tsv file
rows = read_annotation_table(path)

##############################################################################

def retrieve_epmc_publications(pmid):
    
    parameters = {
        "query": pmid, 
        "format": "json",
        "resultType": "core"
        }
    response = requests.get("https://www.ebi.ac.uk/europepmc/webservices/rest/search", params = parameters)
    
    if response.status_code == 200:
        results = response.json()["resultList"]["result"]
        informations = results[0]
    
    return informations

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
          provenance = info
          
   return provenance

##############################################################################

def create_progenetix_posts(rows):

    posts = []
    
    for row in rows:
        pub = {}
        info = retrieve_epmc_publications(row[0]) 
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
                    "sample_types": [],
                    "sortid": None, 
                    "title": title,
                    "year": year
                    })  
        
        pub_copy = pub.copy()
        posts.append(pub_copy)
        
    return posts

posts = create_progenetix_posts(rows) ### posts to be uploaded on MongoDB Progenetix publication collection
for post in posts:
    jprint(post)

##############################################################################

def update_publications(posts):

    ids = cl.distinct("id")
    for post in posts:   
            
        if post["id"] in ids:
            print(post["id"], ": this article is already on the progenetix publications collection.")
            #result = cl.update_one({"id": post["id"]}, {"$set": {"sample_types": [{"id": "NCIT:C96963", ...}]}}) #example of an update that could be done
        else:
            print(post["id"], ": this article isn't on the progenetix publications collection yet.")
            result = cl.insert_one(post)
            result.inserted_id  
    
    
    
    
    
    
    


