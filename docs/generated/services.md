## `/byconschemas`

This helper service reads and serves local schema definition files. The name of
the schema (corresponding to the file name minus extension) is provided either
as an `id` query parameter or as the first part of the path after `schemas/`.

* <https://progenetix.org/services/schemas/biosample>


## `/cnvstats`

==TBD==


## `/collationplots`

The `collationplots` function is a service to provide plots for CNV data aggregated
for samples matching individual filter values such as diagnostic codes or experimental
series id values. The default response is an SVG histogram ("histoplot"). Please refer
to the plot parameters documentation and the `ByconPlot` class for other options.

For a single plot one can provide the entity id as path id value.

#### Examples (using the Progenetix resource as endpoint):

* https://progenetix.org/services/collationplots/pgx:cohort-TCGAcancers
* https://progenetix.org/services/collationplots/?filters=NCIT:C7376,PMID:22824167,pgx:icdom-85003
* https://progenetix.org/services/collationplots/?filters=NCIT:C7376,PMID:22824167&plotType=histoheatplot
* https://progenetix.org/services/collationplots/?collationTypes=icdom&minNumber=1000&plotType=histoheatplot


## `/collations`

The `collations` service provides access to information about data "subsets"
in the project databases. Collations typically are aggregations of samples
sharing an ontology code (e.g. NCIT) or external identifier (e.g. PMID). Therefore,
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


## `/cytomapper`

The `cytomapper` function provides a JSON response with cytoband information
such as matched cytobands and the genome coordinates of their extend.

There is **currently only support for GRCh38**.

#### Response Schema

* <https://progenetix.org/services/schemas/CytobandMapping/>

#### Parameters

* `cytoBands` (path default)
    - a properly formatted cytoband annotation
    - "8", "9p11q21", "8q", "1p12qter"
* or `chroBases`
    - `7:23028447-45000000`
    - `X:99202660`

#### Examples (using the Progenetix resource as endpoint):

* https://progenetix.org/services/cytomapper/8q21q24
* https://progenetix.org/services/cytomapper/13q
* https://progenetix.org/services/cytomapper?chroBases=12:10000000-45000000


## `/dbstats`

This service endpoint provides statistic information about the resource's
datasets.

#### Examples

* <https://progenetix.org/services/dbstats/>
* <https://progenetix.org/services/dbstats/examplez>


## `/endpoints`

The service provides the schemas for the `BeaconMap` OpenAPI endpoints.

#### Examples (using the Progenetix resource as endpoint):

* <https://progenetix.org/services/endpoints/analyses>
* <https://progenetix.org/services/endpoints/biosamples>


## `/genespans`

The `genespans` function provides a JSON response with the coordinates of
matching gene IDs.

#### Examples (using the Progenetix resource as endpoint):

* https://progenetix.test/services/genespans/MYC
* https://progenetix.test/services/genespans/?geneId=MYC


## `/geolocations`

None


## `/ids`

The `ids` service forwards compatible, prefixed ids (see `config/ids.yaml`) to specific
website endpoints. There is no check if the id exists; this is left to the web
page handling itself.

Stacking with the "pgx:" prefix is allowed.

#### Examples (using the Progenetix resource as endpoint):

* <https://progenetix.org/services/ids/pgxbs-kftva5zv>
* <https://progenetix.org/services/ids/PMID:28966033>
* <https://progenetix.org/services/ids/NCIT:C3262>


## `/intervalFrequencies`

None


## `/ontologymaps`

None


## `/pgxsegvariants`

None


## `/publications`

==TBD==


## `/samplemap`

==TBD==


## `/samplematrix`

The service uses the standard bycon data retrieval pipeline with `analysis`
as entity type. Therefore, all standard Beacon query parameters work and also
the path is interpreted for an biosample `id` value if there is an entry at
`.../biosamples/{id}`


## `/sampleplots`

The plot service uses the standard bycon data retrieval pipeline with `biosample`
as entity type. Therefore, all standard Beacon query parameters work and also
the path is interpreted for an biosample `id` value if there is an entry at
`.../sampleplots/{id}`

The plot type can be set with `plotType=samplesplot` (or `histoplot` but that is
the fallback). Plot options are available as usual.

#### Examples (using the Progenetix resource as endpoint):

* http://progenetix.org/services/sampleplots/pgxbs-kftvjv8w
* http://progenetix.org/services/sampleplots/pgxbs-kftvjv8w?plotType=samplesplot&datasetIds=cellz
* http://progenetix.org/services/sampleplots?plotType=samplesplot&datasetIds=cellz&filters=cellosaurus:CVCL_0030
* http://progenetix.org/services/sampleplots?filters=pgx:icdom-81703
* http://progenetix.org/services/sampleplots/?testMode=true&plotType=samplesplot
* http://progenetix.org/services/sampleplots?filters=pgx:icdom-81703&plotType=histoplot&plotPars=plot_chro_height=0::plot_title_font_size=0::plot_area_height=18::plot_margins=0::plot_axislab_y_width=0::plot_grid_stroke=0::plot_footer_font_size=0::plot_width=400
* http://progenetix.org/services/sampleplots?datasetIds=progenetix&plotMinLength=1000&plotMaxLength=3000000&geneId=CDKN2A&variantType=EFO:0020073&plotPars=plotChros=9::plotGeneSymbols=CDKN2A::plotWidth=300&plotType=histoplot


## `/sampletable`

The service uses the standard bycon data retrieval pipeline with `biosample`
as entity type. Therefore, all standard Beacon query parameters work and also
the path is interpreted for an biosample `id` value if there is an entry at
`.../sampletable/{id}`

The table type can be changed with `tableType=individuals` (or `analyses`).

#### Examples

* http://progenetix.org/services/sampletable/pgxbs-kftvjv8w
* http://progenetix.org/services/sampletable?datasetIds=cellz&filters=cellosaurus:CVCL_0030
* http://progenetix.org/services/sampletable?filters=pgx:icdom-81703


## `/services`

The `services` application deparses a request URI and calls the respective
script. The functionality is combined with the correct configuration of a 
rewrite in the server configuration for creation of canonical URLs.


## `/uploader`

This service is used by UI implementations to upload user provided `.pgxseg` files
for visualization of the variants using the packages plotting functions.

As exception to the general rule the `uploader` service does not make use of standard
argument parsing but directly uses `cgi.FieldStorage()` and `....file.read()`.


## `/variantsbedfile`

The `variantsbedfile` function provides a BED file with the matched genomic
variants from a Beacon query or a sample id.

#### Examples

* http://progenetix.org/services/variantsbedfile/pgxbs-kftvjv8w


## `/vcfvariants`

The VCF service uses the standard bycon data retrieval pipeline with `biosample`
as entity type. Therefore, all standard Beacon query parameters work and also
the path is interpreted for an biosample `id` value if there is an entry at
`.../vcfvariants/{id}`

#### Examples

* http://progenetix.org/services/vcfvariants/pgxbs-kftvjv8w


