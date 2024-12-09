from bycon import BYC, BYC_PARS, ByconResultSets, prdbug, print_uri_rewrite_response
from byconServiceLibs import write_variants_bedfile


def variantsbedfile():
    """
    The `variantsbedfile` function provides a BED file with the matched genomic
    variants from a Beacon query or a sample id.

    #### Examples

    * http://progenetix.org/services/variantsbedfile/pgxbs-kftvjv8w
    """
    BYC.update({"request_entity_id": "biosample"})
    rss = ByconResultSets().datasetsResults()
    ds_id = list(rss.keys())[0]
    ucsclink, bedfilelink = write_variants_bedfile(rss, ds_id)
    if "ucsc" in BYC_PARS.get("output", "bed").lower():
        print_uri_rewrite_response(ucsclink, bedfilelink)
    print_uri_rewrite_response(bedfilelink)

