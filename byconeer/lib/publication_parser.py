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
    
    def get_publications(row):
    
    parameters = {
        "query": row[0], #pmid
        "format": "json",
        "resultType": "core"
        }
    response = requests.get("https://www.ebi.ac.uk/europepmc/webservices/rest/search", params = parameters)
    
    if response.status_code == 200:
        results = response.json()["resultList"]["result"]
        info = results[0]
        
        # Get basic informations:
        abstract = info["abstractText"]
        ID = info["pmid"]
        author = info["authorString"]
        journal = info["journalInfo"]["journal"]["medlineAbbreviation"]
        title = info["title"]
        year = info["pubYear"]
        
        # Make label:
        short_author = re.sub(r'(.{2,32}[\w\.\-]+? \w\-?\w?\w?)(\,| and ).*?$', r'\1 et al.', author)
        
        if len(title) <= 100:
            label = short_author + f' ({year}) ' + title
        else:
            label = short_author + f' ({year}) ' + ' '.join(title.split(' ')[:12]) + ' ...'
        
        # Remove HTML formatting:
        abstract_no_html = re.sub(r'<[^\>]+?>', "", abstract)
        title_no_html = re.sub(r'<[^\>]+?>', "", title)
        label_no_html = re.sub(r'<[^\>]+?>', "", label)        
        
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
        
        pub.update({"abstract": abstract_no_html,
                    "authors": author,
                    "counts": counts,
                    "id": "PMID:" + str(ID),
                    "label": label_no_html, 
                    "journal": journal,
                    "sortid": None, 
                    "title": title_no_html,
                    "year": year
                    })  
        
    # Get geolocation:
    where = {"city": row[8]} #city
    location = requests.get("https://progenetix.org/services/geolocations", params = where)
    coordinates = location.json()["response"]["results"]
    
    for info in coordinates:
        if info["id"] == row[9]: #locationID = heidelberg::germany
            provenance = info
    
    pub.update({"provenance": provenance})
    
    return pub

for i, row in enumerate(l):
    if i > 0: # 1st row contains names of columns
        p = get_publications(row)
        jprint(p)



    
 
                

