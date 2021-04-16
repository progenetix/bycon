from os import path
from pymongo import MongoClient
from byconeer.lib.publication_utils import (read_annotation_table, create_progenetix_posts) ### ?

"""
## `publicationUpdater`

"""

dir_path = path.dirname( path.abspath(__file__) ) ### prints the path of the directory where file is found
file_path = path.join(dir_path, 'annotation_test1.txt') ### name of your annotation file (! tab-separated values !)

##############################################################################
##############################################################################
##############################################################################

def main():
    update_publications()

##############################################################################

def update_publications():
    
    # Read annotation table:
    rows = read_annotation_table(file_path)
    
    # Use retrieval to generate posts to be uploaded on MongoDB
    posts = create_progenetix_posts(rows)
    
    # Connect to MongoDB and load publication collection
    client = MongoClient() 
    cl = client['progenetix'].publications
    ids = cl.distinct("id")
    
    # Update the database
    for post in posts:   
            
        if post["id"] in ids:
            print(post["id"], ": this article is already on the progenetix publications collection.")
       
        else:
            print(post["id"], ": this article isn't on the progenetix publications collection yet.")
            result = cl.insert_one(post)
            result.inserted_id  

##############################################################################

if __name__ == '__main__':
        main()

##############################################################################
##############################################################################
##############################################################################
