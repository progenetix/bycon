import requests
import json
import re
from pymongo import MongoClient
import csv

##############################################################################
 
def create_short_publication_label(author="", title="", year=""):
    
    short_author = re.sub(r'(.{2,16}[\w\.\-]+? \w\-?\w?\w?)(\,| and ).*?$', r'\1 et al.', author)

    if len(title) <= 50:
        label = short_author + f' ({year}) ' + title
    else:
        label = short_author + f' ({year}): ' + ' '.join(title.split(' ')[:6]) + '...'
        
    return label
