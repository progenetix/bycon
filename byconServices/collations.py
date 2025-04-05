from bycon import print_json_response
from byconServiceLibs import ByconServiceResponse

def collations():
    """
    The `collations` service provides access to information about data "subsets"
    in the project databases. Collations typically are aggregations of samples
    sharing an ontology code (e.g. NCIT) or external identifier (e.g. pubmed). Therefore,
    in the context of Beacon the collations in `bycon` provide the `filtering_terms`
    available through Beacon queries, but also additional information e.g. about
    child terms and statistics related to the terms.

    In the case of the web projects the main purpose of the `services/collations/
    endpoin is in providing the child terms and path relations for generating ontology
    trees in the UI.

    ### Parameters

    * `collationTypes=...`
    * `includeDescendantTerms=false`
      - only delivers data about codes with direct matches, i.e. excluding such
      where only a child term had a direct match
      - this is especially useful for e.g. getting a fast overview about mappings
      of deeply nested coding systems like `NCIT`
    * `deliveryKeys=...`

    ### Examples

    * <https://progenetix.org/services/collations?deliveryKeys=id,count&collationTypes=cellosaurus>
    * <https://progenetix.org/services/collations?collationTypes=NCIT>
    * <https://progenetix.org/services/collations?collationTypes=NCIT&includeDescendantTerms=false>
    """
    ByconServiceResponse().print_collations_response()
