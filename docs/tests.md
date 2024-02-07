# Endpoint Tests

The endpoint tests here are run against the Progenetix beacon and are also used
to demonstrate path & query options as well as response formats.

## Standard Beacon Paths

We here show examples using the Progenetix instance with its `/beacon/` root path.

### Base `/`

* [/](http://progenetix.org/beacon/)

### `/filtering_terms/`

* [/filtering_terms/](http://progenetix.org/beacon/filtering_terms/)

### `/filtering_terms/` + query

* [/filtering_terms/?filters=PMID](http://progenetix.org/beacon/filtering_terms/?filters=PMID)
* [/filtering_terms/?filters=NCIT,icdom](http://progenetix.org/beacon/filtering_terms/?filters=NCIT,icdom)

### `/biosamples/` + query

* [/biosamples/?filters=cellosaurus:CVCL_0004](http://progenetix.org/beacon/biosamples/?filters=cellosaurus:CVCL_0004)

#### `/biosamples/{id}/`

* [/biosamples/pgxbs-kftva5c9/](http://progenetix.org/beacon/biosamples/pgxbs-kftva5c9/)
  - retrieval of a single biosample

#### `/biosamples/{id}/variants/`

* [/biosamples/pgxbs-kftva5c9/genomicVariations/](http://progenetix.org/beacon/biosamples/pgxbs-kftva5c9/genomicVariations/)

#### `/biosamples/{id}/analyses/`

* [/biosamples/pgxbs-kftva5c9/analyses/](http://progenetix.org/beacon/biosamples/pgxbs-kftva5c9/analyses/)

### Base `/individuals`

#### `/individuals/` + query

* [/individuals/?filters=NCIT:C7541](http://progenetix.org/beacon/individuals/?filters=NCIT:C7541)
* [/individuals/?filters=PATO:0020001,NCIT:C9291](http://progenetix.org/beacon/individuals/?filters=PATO:0020001,NCIT:C9291)

#### `/individuals/{id}/`

* [/individuals/pgxind-kftx25hb/](http://progenetix.org/beacon/individuals/pgxind-kftx25hb/)

#### `/individuals/{id}/variants/`

* [/individuals/pgxind-kftx25hb/genomicVariations/](http://progenetix.org/beacon/individuals/pgxind-kftx25hb/genomicVariations/)

### Base `/variants`

#### `/variants/` + query

* [/variants/?referenceName=refseq:NC_000017.11&variantType=DEL&start=7500000&start=7676592&end=7669607&end=7800000](http://progenetix.org/beacon/genomicVariations/?referenceName=refseq:NC_000017.11&variantType=DEL&start=7500000&start=7676592&end=7669607&end=7800000)
* [/variants/?referenceName=refseq:NC_000017.11&variantType=DEL&start=7500000&start=7676592&end=7669607&end=7800000&requestedGranularity=count](https://progenetix.org/beacon/genomicVariations/?referenceName=refseq:NC_000017.11&variantType=DEL&start=7500000&start=7676592&end=7669607&end=7800000&requestedGranularity=count)
    - same w/ Boolean response
* [/variants/?requestedGranularity=boolean&referenceBases=G&alternateBases=A&referenceName=refseq:NC_000017.11&start=7577120](http://progenetix.org/beacon/genomicVariations/?requestedGranularity=boolean&referenceBases=G&alternateBases=A&referenceName=refseq:NC_000017.11&start=7577120)


#### `/variants/{id}/` or `/g_variants/{id}/`

* [/variants/pgxvar-5f5a35586b8c1d6d377b77f6/](http://progenetix.org/beacon/genomicVariations/pgxvar-5f5a35586b8c1d6d377b77f6/)
* [/g_variants/pgxvar-5f5a35586b8c1d6d377b77f6/](http://progenetix.org/beacon/g_variants/pgxvar-5f5a35586b8c1d6d377b77f6/)

#### `/variants/{id}/biosamples/`

* [/variants/pgxvar-5f5a35586b8c1d6d377b77f6/biosamples/](http://progenetix.org/beacon/genomicVariations/pgxvar-5f5a35586b8c1d6d377b77f6/biosamples/)

### Base `/analyses` (or `/analyses`)

#### `/analyses/` + query

* [/analyses/?filters=cellosaurus:CVCL_0004](http://progenetix.org/beacon/analyses/?filters=cellosaurus:CVCL_0004)
  - this example retrieves all analyses having an annotation for the Cellosaurus _CVCL_0004_
  identifier (K562)

## Non-standard output options `&output=...`

### `&output=histoplot`

* [/beacon/biosamples/?datasetIds=examplez,progenetix,cellz&referenceName=9&variantType=DEL&start=21500000&start=21975098&end=21967753&end=22500000&filters=NCIT:C3058&output=histoplot](http://progenetix.org/beacon/biosamples/?datasetIds=examplez,progenetix,cellz&referenceName=9&variantType=DEL&start=21500000&start=21975098&end=21967753&end=22500000&filters=NCIT:C3058&output=histoplot)

## Beacon Support & Beacon+

### Phenopackets `/biosamples/{id}/phenopackets/` & `/individuals/{id}/phenopackets/`

* [/individuals/pgxind-kftx25hb/phenopackets/](http://progenetix.org/beacon/individuals/pgxind-kftx3fpk/phenopackets/)

### `/aggregator/`

* [http://progenetix.org/beacon/aggregator/?referenceName=refseq:NC_000007.14&start=140753335&alternateBases=A&assemblyId=GRCh38&responseEntityId=genomicVariant](http://progenetix.org/beacon/aggregator/?referenceName=refseq:NC_000007.14&start=140753335&alternateBases=A&assemblyId=GRCh38&responseEntityId=genomicVariant)

## Query examples

### Filter use

### Region query with positive and excluded filter

In this example we use a filter negation by having a `!` prefixed `PATO:0020002`
resulting in a 

* [/beacon/biosamples/?requestedGranularity=count&datasetIds=progenetix&referenceName=refseq:NC_000009.12&variantType=EFO:0030067&start=21500000&start=21975098&end=21967753&end=22500000&filters=!PATO:0020002,NCIT:C3058](http://progenetix.org/beacon/biosamples/?requestedGranularity=count&datasetIds=progenetix&referenceName=refseq:NC_000009.12&variantType=EFO:0030067&start=21500000&start=21975098&end=21967753&end=22500000&filters=!PATO:0020002,NCIT:C3058)


