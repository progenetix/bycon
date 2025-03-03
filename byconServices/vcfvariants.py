from bycon import BYC, ByconResultSets
from byconServiceLibs import PGXvcf

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
    f_d = ByconResultSets().get_flattened_data()
    PGXvcf(f_d).stream_pgxvcf()
