from bycon import *
from byconServiceLibs import PGXseg

"""
The service uses the standard bycon data retrieval pipeline with `biosample`
as entity type. Therefore, all standard Beacon query parameters work and also
the path is interpreted for an biosample `id` value if there is an entry at
`.../pgxsegvariants/{id}`

* http://progenetix.org/services/pgxsegvariants/pgxbs-kftvjv8w

"""

def pgxsegvariants():
    rss = ByconResultSets().datasetsResults()
    ds_id = list(rss.keys())[0]
    PGXseg(rss, ds_id).stream_pgxseg()
