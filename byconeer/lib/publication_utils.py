import requests
import json
import re
from pymongo import MongoClient
import csv

##############################################################################
 
def create_short_publication_label(author="", title="", year=""):

    authors_max_characters = 16
    title_max_words = 9
    title_max_length = 60
    
    short_author = re.sub(r'(.{2,'+str(authors_max_characters)+'}[\w\.\-]+? \w\-?\w?\w?)(\,| and ).*?$', r'\1 et al.', author)

    if len(title) <= title_max_length:
        label = short_author + f' ({year}) ' + title
    else:
        label = short_author + f' ({year}): ' + ' '.join(title.split(' ')[:title_max_words]) + '...'
        
    return label
