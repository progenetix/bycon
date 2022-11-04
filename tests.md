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

* [/variants/?assemblyId=GRCh38&referenceName=17&variantType=DEL&filterLogic=AND&start=7500000&start=7676592&end=7669607&end=7800000](http://progenetix.org/beacon/variants/?assemblyId=GRCh38&referenceName=17&variantType=DEL&filterLogic=AND&start=7500000&start=7676592&end=7669607&end=7800000)

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


## Services

### Beacon Support

### Beyond Beacon Services

#### `/geolocations/`

##### Map Projections of Query results

* [/services/geolocations?city=Heidelberg&output=map&marker_type=marker](http://progenetix.org/services/geolocations?city=Heidelberg&output=map&marker_type=marker)





