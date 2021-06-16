<!--podmd-->
## _collations_

* provides access to information about data "subsets" in the Progenetix project
databases
  - typically aggregations of samples sharing an ontology code (e.g. NCIT) or 
  external identifier (e.g. PMID)

#### Parameters

##### `methods`

* `counts`
* `codematches`
  - only delivers data about codes with direct matches, i.e. excluding such
  where only a child term had a direct match
  - this is especially useful for e.g. getting a fast overview about mappings
  of deeply nested coding systems like `NCIT`

#### Examples

* <http://progenetix.org/services/collations?deliveryKeys=id,count&filters=cellosaurus&datasetIds=progenetix>
* <https://progenetix.org/services/collations?filters=NCIT>
* <https://progenetix.org/services/collations?filters=NCIT&method=codematches>
* <http://progenetix.org/cgi-bin/bycon/bin/collations.py?filters=NCIT&datasetIds=progenetix&method=counts>
* <https://progenetix.org/services/collations?filters=icdom&method=codes&output=text>

<!--/podmd-->
