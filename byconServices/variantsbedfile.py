from bycon import (
    BYC,
    BYC_PARS,
    ByconResultSets,
    prdbug,
    print_uri_rewrite_response
)
from byconServiceLibs import PGXbed

def variantsbedfile():
    """
    The `variantsbedfile` function provides a BED file with the matched genomic
    variants from a Beacon query or a sample id. Since the UCSC browser only
    displays one reference (chromosome) this methos is intended to be used upon
    specific variant queries, though.

    The service uses the standard bycon data retrieval pipeline with genomic
    variants as the response entity type. Therefore, standard Beacon variant queries
    will work as well as single `...id` values for specific samples.

    #### Examples

    * http://progenetix.org/services/variantsbedfile/?datasetIds=progenetix&variantType=EFO:0030067&referenceName=refseq:NC_000009.12&start=21000000&start=21975098&end=21967753&end=23000000&filters=NCIT:C3058&limit=50&output=ucsc
    * http://progenetix.org/services/variantsbedfile/?datasetIds=progenetix&geneId=CDKN2A&variantMaxLength=1000000&filters=NCIT:C3058&limit=50&output=ucsc

    """

    f_d = ByconResultSets().get_flattened_data()
    BED = PGXbed(f_d)
    if "ucsc" in BYC_PARS.get("output", "bed").lower():
        print_uri_rewrite_response(BED.bed_ucsc_link())
    print_uri_rewrite_response(BED.bedfile_link())

