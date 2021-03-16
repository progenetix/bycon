import re

################################################################################

def generate_publication_label(pub):

    label = ""

    if "authors" in pub:
        pa = pub["authors"].copy()

    # ...

    
    pub.update({"label": label})

    return pub

