from bycon import BYC, ByconResultSets
from byconServiceLibs import export_vcf_download

################################################################################

def vcfvariants():
    """
    The VCF service uses the standard bycon data retrieval pipeline with `biosample`
    as entity type. Therefore, all standard Beacon query parameters work and also
    the path is interpreted for an biosample `id` value if there is an entry at
    `.../vcfvariants/{id}`

    #### Examples

    * http://progenetix.org/services/vcfvariants/pgxbs-kftvjv8w
    """
    # TODO: Fix this, to be correctly read from services_entity_defaults
    BYC.update({"request_entity_id": "biosample"})
    rss = ByconResultSets().datasetsResults()
    # Note: only the first dataset will be exported ...
    ds_id = list(rss.keys())[0]
    export_vcf_download(rss, ds_id)
