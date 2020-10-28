import re
from pymongo import MongoClient
from progress.bar import Bar

################################################################################

def dataset_count_collationed_filters(ds_id, **byc):

    mongo_client = MongoClient( )
    mongo_db = mongo_client[ ds_id ]
    bios_coll = mongo_db[ 'biosamples' ]

    sample_no =  bios_coll.estimated_document_count()

    filter_v = [ ]

    scopes = ( "external_references", "biocharacteristics")

    split_v = re.compile(r'^(\w+?)[\:\-].+?$')

    for s in scopes:
        pfs = { }
        source_key = s+".type.id"
        afs = bios_coll.distinct( source_key )
        for k in afs:
            # print(k)
            try:
                if split_v.match(k):
                    pre = split_v.match(k).group(1)

                    if pre in byc["config"]["collationed"]:
                        coll_p = re.compile( byc["config"]["collationed"][ pre ]["pattern"] )
                        if coll_p.match(k):
                            pfs.update( { k: { 
                                "id": k,
                                "count": 0,
                                # "source": byc[ "filter_definitions" ][ pre ][ "name" ],
                                "scope": s
                            } } )
            except:
                continue
        scopedNo = len(pfs.keys())
        if scopedNo > 0:
            bar = Bar(ds_id+': '+s, max = sample_no, suffix='%(percent)d%%'+" of "+str(sample_no) )
            for sample in bios_coll.find({}):
                bar.next()
                if s in sample:
                    for term in sample[ s ]:
                        tid = term["type"]["id"]
                        if tid in pfs.keys():
                            pfs[ tid ]["count"] += 1
                            if "label" in term["type"]:
                                 pfs[ tid ]["label"] = term["type"]["label"]

            bar.finish()

            print("=> {} valid filtering terms out of {} for {} ({})".format(scopedNo, len(afs), s, ds_id) )

            for fk, ft in pfs.items():
                # print("{}: {}".format(ft["id"], ft["count"]))
                filter_v.append(ft)

    print("=> {} filtering terms for {}".format(len(filter_v), ds_id) )
 
    return filter_v
