from bycon import ByconResultSets
from byconServiceLibs import GenomeBins, export_callsets_matrix

def samplematrix():
    """
    The service uses the standard bycon data retrieval pipeline with `analysis`
    as entity type. Therefore, all standard Beacon query parameters work and also
    the path is interpreted for an biosample `id` value if there is an entry at
    `.../biosamples/{id}`
    """
    GenomeBins()
    rss = ByconResultSets().datasetsResults()
    # TODO: right now only the first dataset will be exported ...
    ds_id = list(rss.keys())[0]
    export_callsets_matrix(rss, ds_id)
