<!--podmd-->
## _collations_

* provides access to information about data "subsets" in the Progenetix project
databases
  - typically aggregations of samples sharing an ontology code (e.g. NCIT) or 
  external identifier (e.g. PMID)

#### Parameters

* `includeDescendantTerms=false`
  - only delivers data about codes with direct matches, i.e. excluding such
  where only a child term had a direct match
  - this is especially useful for e.g. getting a fast overview about mappings
  of deeply nested coding systems like `NCIT`

#### Examples

* <http://progenetix.org/services/collations?deliveryKeys=id,count&filters=cellosaurus&datasetIds=progenetix>
* <https://progenetix.org/services/collations?filters=NCIT>
* <https://progenetix.org/services/collations?filters=NCIT&includeDescendantTerms=false>

<!--/podmd-->
