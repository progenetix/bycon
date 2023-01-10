# Tests

## Beacon

### Standard Beacon Paths

#### Base `/`

* [/](http://progenetix.org/beacon/)

#### `/filtering_terms/`

* [/filtering_terms/](http://progenetix.org/beacon/filtering_terms/)

#### `/filtering_terms/` + query

* [/filtering_terms/?filters=PMID](http://progenetix.org/beacon/filtering_terms/?filters=PMID)
* [/filtering_terms/?filters=NCIT,icdom](http://progenetix.org/beacon/filtering_terms/?filters=NCIT,icdom)

#### `/biosamples/` + query

* [/biosamples/?filters=cellosaurus:CVCL_0004](http://progenetix.org/beacon/biosamples/?filters=cellosaurus:CVCL_0004)

##### `/biosamples/{id}/`

* [/biosamples/pgxbs-kftva5c9/](http://progenetix.org/beacon/biosamples/pgxbs-kftva5c9/)
  - retrieval of a single biosample

##### `/biosamples/{id}/variants/`

* [/biosamples/pgxbs-kftva5c9/variants/](http://progenetix.org/beacon/biosamples/pgxbs-kftva5c9/variants/)

##### `/biosamples/{id}/analyses/`

* [/biosamples/pgxbs-kftva5c9/analyses/](http://progenetix.org/beacon/biosamples/pgxbs-kftva5c9/variants/)

#### Base `/individuals`

##### `/individuals/` + query

* [/individuals/?filters=NCIT:C7541](http://progenetix.org/beacon/individuals/?filters=NCIT:C7541)
* [/individuals/?filters=PATO:0020001,NCIT:C9291](http://progenetix.org/beacon/individuals/?filters=PATO:0020001,NCIT:C9291)

##### `/individuals/{id}/`

* [/biosamples/pgxind-kftx25hb/](http://progenetix.org/beacon/biosamples/pgxind-kftx25hb/)

##### `/individuals/{id}/variants/`

* [/individuals/pgxind-kftx25hb/variants/](http://progenetix.org/beacon/individuals/pgxind-kftx25hb/variants/)

#### Base `/variants`

##### `/variants/` + query

* [/variants/?referenceName=refseq:NC_000017.11&variantType=DEL&start=7500000&start=7676592&end=7669607&end=7800000](http://progenetix.org/beacon/variants/?referenceName=refseq:NC_000017.11&variantType=DEL&start=7500000&start=7676592&end=7669607&end=7800000)
* [/variants/?referenceName=refseq:NC_000017.11&variantType=DEL&start=7500000&start=7676592&end=7669607&end=7800000&requestedGranularity=boolean](http://progenetix.org/beacon/variants/?referenceName=refseq:NC_000017.11&variantType=DEL&start=7500000&start=7676592&end=7669607&end=7800000&requestedGranularity=boolean)
    - same w/ Boolean response
* [/variants/?requestedGranularity=boolean&referenceBases=G&alternateBases=A&referenceName=refseq:NC_000017.11&start=7577120](http://progenetix.org/beacon/variants/?requestedGranularity=boolean&referenceBases=G&alternateBases=A&referenceName=refseq:NC_000017.11&start=7577120)


##### `/variants/{id}/` or `/g_variants/{id}/`

* [/variants/5f5a35586b8c1d6d377b77f6/](http://progenetix.org/beacon/variants/5f5a35586b8c1d6d377b77f6/)
* [/g_variants/5f5a35586b8c1d6d377b77f6/](http://progenetix.org/beacon/g_variants/5f5a35586b8c1d6d377b77f6/)

##### `/variants/{id}/biosamples/`

* [/variants/5f5a35586b8c1d6d377b77f6/biosamples/](http://progenetix.org/beacon/variants/5f5a35586b8c1d6d377b77f6/biosamples/)

#### Base `/analyses` (or `/callsets`)

##### `/analyses/` + query

* [/analyses/?filters=cellosaurus:CVCL_0004](http://progenetix.org/beacon/analyses/?filters=cellosaurus:CVCL_0004)
  - this example retrieves all biosamples having an annotation for the Cellosaurus _CVCL_0004_
  identifier (K562)

### Beacon Support & Beacon+

##### `/biosamples/{id}/phenopackets/`


##### `/individuals/{id}/phenopackets/`

* [/individuals/pgxind-kftx25hb/phenopackets/](http://progenetix.org/beacon/individuals/pgxind-kftx3fpk/phenopackets/)

#### `/aggregator/`

* [http://progenetix.org/beacon/aggregator/?referenceName=refseq:NC_000007.14&start=140753335&alternateBases=A&assemblyId=GRCh38&responseEntityId=genomicVariant](http://progenetix.org/beacon/aggregator/?referenceName=refseq:NC_000007.14&start=140753335&alternateBases=A&assemblyId=GRCh38&responseEntityId=genomicVariant)

## Services

### Beyond Beacon Services

#### `/geolocations/`

##### Map Projections of Query results

The option `output=map` activates a Leaflet-based map projection of 
the geomapping data (either from search results or provided as an
external, web hosted file).

* [/services/geolocations?city=Heidelberg&output=map&marker_type=marker](http://progenetix.org/services/geolocations?city=Heidelberg&output=map&marker_type=marker)

##### Map with markers from a hosted file

* [progenetix.org/services/geolocations?map_w_px=600&map_h_px=480&marker_type=marker&file=https://raw.githubusercontent.com/compbiozurich/compbiozurich.github.io/main/collab/people.tab&output=map&help=true](http://progenetix.org/services/geolocations?map_w_px=600&map_h_px=480&marker_type=marker&file=https://raw.githubusercontent.com/compbiozurich/compbiozurich.github.io/main/collab/people.tab&output=map&help=true)


#### `/genespans/`

##### Exact gene match

* [/services/genespans/TP53](http://progenetix.org/services/genespans/TP53)


