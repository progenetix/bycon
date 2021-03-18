import requests
import json
import re
import csv

l = []
with open("/Users/sofiapfund/Desktop/Internship/Scripts/publications.txt") as f: # file that contains tab-separated annotations (pmid, counts, city, ...)
   rd = csv.reader(f, delimiter="\t", quotechar='"')
   for row in rd:
        l.append(row)

########################################################################################
      
def jprint(obj):
    text = json.dumps(obj, sort_keys= True, indent = 4, ensure_ascii = False)
    print(text)

########################################################################################

pub = {}

def get_publications(pmid):
    
    parameters = {
        "query": pmid, 
        "format": "json",
        "resultType": "core"}
    response = requests.get("https://www.ebi.ac.uk/europepmc/webservices/rest/search", params = parameters)
    
    if response.status_code == 200:
        results = response.json()["resultList"]["result"]
        info = results[0]
        
        abstract = info["abstractText"]
        ID = info["pmid"]
        author = info["authorString"]
        journal = info["journalInfo"]["journal"]["medlineAbbreviation"]
        title = info["title"]
        year = info["pubYear"]
        
        abstract_no_html = re.sub(r'<[^\>]+?>', "", abstract)
        title_no_html = re.sub(r'<[^\>]+?>', "", title)
        
        pub.update({"abstract": abstract_no_html,
                         "authors": author,
                         "id": "PMID:" + str(ID),
                         "journal": journal,
                         "sortid": None, 
                         "title": title_no_html,
                         "year": year})  
    
    return pub

for i, row in enumerate(l):
    if i > 0: # 1st row contains names of columns
        p = get_publications(row[0])
        #jprint(p)

########################################################################################

def get_geolocation(city, locationID):
    
    where = {"city": city}
    location = requests.get("https://progenetix.org/services/geolocations", params = where)
    coordinates = location.json()["response"]["results"]
    
    for info in coordinates:
        if info["id"] == locationID: #locationID = heidelberg::germany
            provenance = info
    
    pub.update({"provenance": provenance})
    
    return pub

for i, row in enumerate(l):
    if i > 0: # 1st row contains names of columns
        p = get_geolocation(row[8], row[9])
        #jprint(p)

########################################################################################  
    
def fill_counts(row):
    
    counts = {}
    counts.update({"acgh": row[1],
                    "arraymap": 0,
                    "ccgh": row[2],
                    "genomes": row[3],
                    "ngs": row[4],
                    "progenetix": row[5],
                    "wes": row[6],
                    "wgs": row[7]})
    
    pub.update({"counts": counts})
    
    return pub

for i, row in enumerate(l):
    if i > 0: # 1st row contains names of columns
        p = fill_counts(row)
        jprint(p)

########################################################################################     
                
def generate_publication_label(pub): # still working on this - use REs

    label = ""

    if "authors" in pub:
        pa = pub["authors"].copy()
        title = pub["title"].copy()
        year = pub["year"].copy()
        
        lab = pa[:50] + f' et al. ({year}): ' 
        
        if len(title) <= 100:
            label = lab + title
        else:
            label = lab + ' '.join(title.split(' ')[:12]) + ' ...'
        
    pub.update({"label": label})

    return pub
