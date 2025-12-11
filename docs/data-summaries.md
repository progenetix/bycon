# Data Summaries ("Aggregations")

## Overview

!!! warning

    This is the work in progress for a general aggregation/summary documentation.
    The most recent version is currently maintained at [bycon.progenetix.org/data-summaries/](https://bycon.progenetix.org/data-summaries/).

Data summaries (also referred to as "aggregations") are summary statistics delivered
beacons. They can reflect different aspects of the beacon's content, such as:

* static overview of the content of a resource
* content of the resources's collections (datasets or cohorts in the Beacon model)
* dynamically generated summaries of query results

Typical summaries reflect the count of value occurrences for individual properties,
or the intersection of two properties (2-dimensional aggregations).

!!! info "Further Info"

    * [Proposals for Aggregated Response](https://github.com/ga4gh-beacon/beacon-v2/discussions/238)

#### Scope of the summary counts

*TODO*: Do the counts have to be projected to the requested entity, or can they
be reported on basis of pre-defined entities (e.g. can a request to `/individuals/`
report the numbers for the matched sample histologies or the individuals with the
matched histologies?.

## General Structure and Calling

Aggregation responses or summary data are called by setting the `requestedGranularity`
to `aggregated`. Example:

* TCGA cancer samples in Progenetix
    - <https://progenetix.org/beacon/biosamples/?requestedGranularity=aggregated&filters=pgx:cohort-TCGAcancers>
    
The aggregation types to be returned can be specified by using the additional
request `aggregationTerms` parameter as well as optional parameters for binning or
term selection (==TBD==). Example:

* Age groups labeled by sex for TCGA cancer individuals in Progenetix
    - <https://progenetix.org/beacon/biosamples/?requestedGranularity=aggregated&filters=pgx:cohort-TCGAcancers&aggregationTerms=ageAtDiagnosisBySex>
    

## Components

Empowering aggregation responses or summary data relies on several components:

* aggregation schema definitions
* internal handling of aggregation pipelines
* a response format for supported aggregations (similar to exposing `filtering_terms`)
* a response format for the summaries
* request parameters for selecting aggregation types
    - additional request parameters for modifying responses (e.g. limits, binning...)
* the front end logic - which is not part of this itself but serves for understanding
  requirements and test formats

??? question "Why not using `filters` as aggregation terms?"

    While it would be possible to use `filters` to define aggregation terms,
    this would lead to confusion as filters are primarily used to define
    query constraints. Additionally filters have different formats which
    would be problematic to handle in aggregation contexts:

    * `ontologyTerm` filter are a type of "valued filters" where a the aggregation
      on the filtering term would lead to a single count response; _i.e._ all the
      different terms existing at the property would have to be indicated
    * `alphanumeric` filters consist of `id` (mapping to a concept), an `operator`
      and a `value`; here an aggregation would only make sense on the `concept`
      part with or without indicators for a binning of the values but not by providing
      the values themselves.

    Therefore, a separate, property based mechanism for defining aggregation
    terms is preferred.


### Aggregation Schema Definitions

Aggregation schema definitions are necessary to define the types of aggregations
supported by a Beacon implementation. These definitions should include:

* the `id` of the aggregation
* a `label`, e.g. used as a title in visualisations
* a `description` of what the aggregation represents, e.g. used for info tooltips
* the `concepts` involved in the aggregation
    - usually one or 2 ("dimensions"); see below
* additional `parameters` for modifying the aggregation behaviour or indicating
  behavior
    - `sorted: true` can indicate to a client that a response has a predefined order
    
#### Concept definitions and parameters

Each `concept` involved in an aggregation should be defined with:

* the `scope`, _i.e._ the respective entity in the data model
* the `property`, _i.e._ property in the respective entity to be aggregated
    - TODO: Defining it as "concept" (e.g. `diseases.diseaseCode`) or specific
      field (`diseases.diseaseCode.id`)? The latter seems more stringent.
* optional modifiers:
    - `termIds` for specifying specific terms to be included in the aggregation
    - `splits` for specifying how to split the aggregation (e.g. binning for
      numeric or seudo-numeric values such as ISO8601 durations for ages)
        * ATM `splits` seem as the best way to specify binning, but this might
          be changed later on.
        * `splits` also correspond nicely to database aggregation concepts such
          as `$buckets` and `$splits` in MongoDB

### Examples

#### Single property aggregation

```
id: sampleOriginDetails
label: Anatomical Origin
description: >-
  Count of anatomical sites in matched biosamples
concepts:
  - property: biosample.sample_origin_detail.id
```

#### Single property aggregation with `splits`

The following example includes pre-defined age group splits which can be overridden by a request parameter (to be defined; probably best to have it in a POST object):

```
id: ageAtSampleCollection
label: Age at Sampling
description: >-
  Age at collection of the sample
sorted: True
concepts:
  - property: biosample.collectionMoment
    splits:
      - P0D
      - P18M
      - P18Y
      - P40Y
      - P65Y
      - P80Y
      - P120Y
```

#### Single property aggregation with `termIds`

```
id: selectedCarinomaDiagnoses
label: Selected Diagnostic Classes (carcinomas; by NCIT)
description: >-
  Count of histological diagnoses in matched biosamples for selected carcinomas
scope: biosample
concepts:
  - property: biosample.histological_diagnosis.id
    termIds:
      - NCIT:C9384 # Kidney Carcinoma
      - NCIT:C3513 # Esophageal Carcinoma
      - NCIT:C35850 # Head and Neck Carcinoma
      - NCIT:C4878 # Lung Carcinoma
      - NCIT:C207229 # Pancreatic Carcinoma
      - NCIT:C4911 # Gastric Carcinoma
      - NCIT:C2955 # Colorectal Carcinoma
      - NCIT:C7927 # Liver Carcinoma
```

#### 2-dimensional aggregation

```
id: diseaseBySex
label: Sex distributions for Diseases
description: 
  - ICD-O 3 histologies by sex in matched biosamples
concepts:
  - property: individual.diseases.diseaseCode.id
  - property: individual.sex.id
```

