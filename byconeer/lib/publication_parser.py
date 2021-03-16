import re

################################################################################

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
        
        #label_no_html = re.sub(r'<[^\>]+?>', "", label) #is this formatting necessary?

    pub.update({"label": label})

    return pub

