from os import path
from pymongo import MongoClient
from byconeer.lib.publication_utils import (read_annotation_table, create_progenetix_posts) ### do I import them like this?

"""
## `publicationUpdater`

"""

##############################################################################
##############################################################################
##############################################################################

def _get_args():
    parser = argparse.ArgumentParser(description="Read publication annotations, create MongoDB posts and update the database.")
    parser.add_argument("-f", "--filepath", help="Path of the .tsv file containing the annotations on the publicationßs.", type=str)
    args = parser.parse_args()
    return args

##############################################################################

def main():
    update_publications()

##############################################################################

def update_publications():

    file_path = _get_args()

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
