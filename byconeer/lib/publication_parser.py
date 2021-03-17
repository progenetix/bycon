import requests
import json
import re

################################################################################

pub = {}

def get_publications(pmid):
    
    parameters = {
        "query": str(pmid), 
        "format": "json",
        "resultType": "core"}
    response = requests.get("https://www.ebi.ac.uk/europepmc/webservices/rest/search", params = parameters)
    results = response.json()["resultList"]["result"]
       
    for el in results:
        abstract = el["abstractText"]
        author = el["authorString"]
        ID = el["pmid"]
        journalInfo = el["journalInfo"]
        journal = journalInfo["journal"]
        medlineAbbreviation = journal["medlineAbbreviation"]
        title = el["title"]
        year = el["pubYear"]
    
        abstract_no_html = re.sub(r'<[^\>]+?>', "", abstract)
        title_no_html = re.sub(r'<[^\>]+?>', "", title)
    
    pub.update({"abstract": abstract_no_html,
                "authors": author,
                "id": "PMID:" + str(ID),
                "journal": medlineAbbreviation,
                "sortid": None, 
                "status" : pub[10],
                "title": title_no_html,
                "year": year})    
    
    return pub


def get_geolocation(city, locationID):
    
    where = {"city": city}
    location = requests.get("https://progenetix.org/services/geolocations", params = where)
    coordinates = location.json()["response"]["results"]
    
    for info in coordinates:
        if info["id"] == locationID: # e.g. locationID = heidelberg::germany
            provenance = info
    
    pub.update({"provenance": provenance})
    
    return pub
   
    
def fill_counts(pmid):
    
    counts = {}
    
    #...
    
    pub.update({"counts": counts})
    
    return pub
        
        
def generate_publication_label(pub):

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
