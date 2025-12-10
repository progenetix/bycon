# Data Summaries ("Aggregations")

!!! note "WiP - To be edited"

    This is the work in progress for a general aggregation/summary documentation.

#### Further Info

* [Proposals for Aggregated Response](https://github.com/ga4gh-beacon/beacon-v2/discussions/238)

## General Structure, Calling and Scope

Aggregation responses or summary data are called by setting the `requestedGranularity`
to `true`. Example:

* <https://progenetix.org/beacon/biosamples/?filters=pgx:icdom-81303&requestedGranularity=aggregated>

#### Scope of the summary counts

*TODO*: Do the counts have to be projected to the requested entity, or can they
be reported on basis of pre-defined entities (e.g. can a request to `/individuals/`
report the numbers for the matched sample histologies or the individuals with the
matched histologies?).

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

#### Examples

##### Simple aggregation

```
id: sampleOriginDetails
label: Anatomical Origin
description: >-
  Count of anatomical sites in matched biosamples
concepts:
  - property: biosample.sample_origin_detail.id
```

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

##### 2-dimensional aggregation

```
id: diseaseBySex
label: Sex distributions for Diseases
description: 
  - ICD-O 3 histologies by sex in matched biosamples
concepts:
  - property: individual.diseases.diseaseCode.id
  - property: individual.ex.id
```

