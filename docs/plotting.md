---
title: Plotting
---

## `byconaut` Plot functionality

Starting with version v1.0.30 (2023-04-14) the `bycon` package added the ability
to produce the typical _Progenetix_-style CNV histograms and CNV sample plots,
later (`bycon` v.1.3.4) moved to the `byconaut` repository.

### Plotting services

Plotting "services" are online service endpoints for generating visualizations
of mostly CNV data from the databases of the respective beaconized resources. In 
the case of the developers these would be e.g. [progenetix.org](https://progenetix.org)
and [cancercelllines.org](https://cancercelllines.org) whcich also are being used
for the active examples below. The plotting services - which are maintained inside
`byconaut/services` but installed in the corresponding webserver CGI directory -
are:

* `services/collationplots/`
* `services/sampleplots/`

### Plotting Applications

Plotting "applications" provide command line utilities for the plotting of database
content and local files. These are maintained in the `byconaut/bin` directory:

* `bin/collationsPlotter.py`
* `bin/samplesPlotter.py`
* `bin/pgxsegPlotter.py`

### Plotting Functionality

Plots can now be generated:

* for samples and aggregated data using standard Beacon v2 query parameters and
  filters, through special `/services/...` endpoints
    - `/services/collationplots` for pre-computed frequency histograms and heatstrips
    - `/services/sampleplots` for query-derived sample plots (including histograms)
        * plot selection through `plotType=` with options `histoplot`, `samplesplot` and `histoheatplot`
        * defaults to `histoplot` if unspecified
* for files uploaded through the Progenetix [`Upload...`](https://progenetix.org/service-collection/uploader/) interface (not terribly stable...)
* through commabnd line scripts in this project's `bin` directory, e.g. for provided
  `.pgxseg` ... files

!!! warning "Custom syntax for plot parameters"

    To limit the amount of pre-defined parameters accepted through the `bycon`
    interface we are using a special syntax for plot parameters. Plot parameters
    (see below for all pre-defined ones) are provided as a single string to `plotPars`
    parameter, with individual parameter pairs concatenated by `::`
        * in GET: `plotPars=plot_chros=8,9,17::labels=8:120000000-123000000:Some+Interesting+Region::plot_gene_symbols=MYCN,TP53,MTAP,CDKN2A,MYC,ERBB2::plot_width=800`
        * in CMD: `--plotPars "plot_chros=8,9,17::labels=8:120000000-123000000:Some Interesting Region::plot_gene_symbols=MYCN,TP53,MTAP,CDKN2A,MYC,ERBB2::plot_width=800"`


### Plot types

#### CNV histograms of collations - `/services/collationplots`

CNV histograms can be generated either (fast) for one or multiple of the "collations" _i.e._
samples sharing a common code (diagnosis, technnique...) or identifier (cell line id, 
PMID ...), or as single histogram for the output of a Beacon query.

A complete list of collations can be retrieved through the `/services/collations/`
endpoint, e.g. [/services/collations?datasetIds=progenetix](http://progenetix.org/services/collations?datasetIds=progenetix) - an option `&output=text` should provide this as a table instead of Beacon-style JSON response.

Please note that the `datasetIds` parameter will fall back to the default parameter
if not indicated.

##### Examples

The examples below link to {{config.api_site_label}}.

* [/services/collationplots/?filters=NCIT:C35562,NCIT:C3709]({{config.api_web_root}}/services/collationplots/?filters=NCIT:C35562,NCIT:C3709)
    - a combination of 2 histograms
* [/services/collationplots?filters=NCIT:C35562,NCIT:C3709&datasetIds=progenetix,cellz](https://progenetix.org/services/collationplots?filters=NCIT:C35562,NCIT:C3709&datasetIds=progenetix,cellz)
    - a combination of 2 histograms
* [/services/collationplots/?filters=pgx:icdom-85003,pgx:icdom-81703,pgx:icdom-87003,pgx:icdom-87203,pgx:icdom-94003,pgx:icdom-95003,pgx:icdom-81403&plotPars=plot_title=CNV+Comparison::plot_area_height=50::plot_axis_y_max=80::plot_label_y_values=50](https://progenetix.org/services/collationplots/?filters=pgx:icdom-85003,pgx:icdom-81703,pgx:icdom-87003,pgx:icdom-87203,pgx:icdom-94003,pgx:icdom-95003,pgx:icdom-81403&plotPars=plot_title=CNV+Comparison::plot_area_height=50::plot_axis_y_max=80::plot_label_y_values=50)
    - a collations based example showing the use of some extra parameters such as
        * `plot_title`
        * `plot_area_height`
        * `plot_axis_y_max` & `plot_label_y_values`

#### CNV sample plots - `/services/sampleplots`

Sample selection based plotting uses the standard bycon query stack for sample retrieval
(_i.e._ aggregation over the data model) and then generates CNV plots from the found
samples, either as clustered individual profiles or as binned frequency plot data (histograms or heatstrips).

**CAVE**: Sample plots may be time consuming due to the retrieval and plotting of
all variants per sample. Therefore, usually a limit (default or via Beacon `limit`
parameter) is being applied.

##### Examples

* [/services/sampleplots?filters=pgx:icdom-95003&plotPars=plot_filter_empty_samples=y::plotGeneSymbols=MYCN::plotType=samplesplot&limit=100](https://progenetix.org/services/sampleplots?filters=pgx:icdom-95003&plotPars=plot_filter_empty_samples=y::plotGeneSymbols=MYCN::plotType=samplesplot&limit=100)
    - this example is based on the histoplot example above, but based on individual
      sample retrieval and plotting and with some plot modifications:
        * limits the output to 100 samples (`limit=100`)
        * removes samples w/o CNVs (`plot_filter_empty_samples=y`)
* [/services/sampleplots?filters=pgx:icdom-95003&plotPars=plotGeneSymbols=MYCN&limit=100&plotType=samplesplot](https://progenetix.org/services/sampleplots?filters=pgx:icdom-95003&plotPars=plotGeneSymbols=MYCN::limit=100&plotType=samplesplot)
    - this example gets samples for ICD-O Morphology 95003/3 (a.k.a. `pgx:icdom-95003`)
    - limits the output to the first 1000 samples (`limit=1000`)
    - adds a label for the **MYCN** gene
* [/services/sampleplots?filters=pgx:icdom-95003&plotPars=plotGeneSymbols=MYCN&limit=100](http://progenetix.org/services/sampleplots?filters=pgx:icdom-95003&plotPars=plotGeneSymbols=MYCN&limit=100)
    - this is the same selection and labeling but defaulting to the `histoplot`
      option since no `plotType` parameter is indicated


## Plot parameters

Plot parameters can be given both in `snake_case` and in the corresponding
`camelCase` format (`plot_area_width` or `plotAreaWidth`). Please see the box
above for the concatenation syntax!

A detailed list of plot parameters is provided [on this page](/generated/plot_defaults/).

<!-- 
### Parameter definitions

``` yaml title="Plot parameters"
--8<-- "./local/plot_defaults.yaml"
``` -->