# Importing Data

Importing and updating of data for `bycon` databases is discussed in
this section. The relevant apps can be found in the `importers` directory
in the project's root.

The workflows discussed here assume that the database is already set up.

## Import Table Formats

Importing new sample data alwaays requires the initial import of
_analysis_ data, _i.e._ at least an experimental identifier which then acts as
a reference for the genomic variants.

The importers are designed to handle a tab-delimited data file
in which the first line contains column headers which have to correspond
to values in the `datatable_definitions.yaml` file. However, it is not necessary to
create separate files for all `analyses` & `biosamples` & `individuala`
entities; the importers will handle the data in a single file
which makes sense when having singular relation 1 individual => 1 biosample => 1 analysis (=> n variants).

## Workflow

### 1. Create a import tables

Run the `importers/importTablesGenerator.py` script to create empty import tables.
You will be asked to provide an (optional) directory path and the number of analyses
to be imported. This number is used to provide unique, linked identifiers for the
metadata entities (analyses, biosamples, individuals). Probably the `metadata.tsv`
table will be enough but there are separate tables for te different entities with
all supported parameters.

### 2. Fill in the metadata tables

#### Identifiers

* stick with the provided ones or replace them with your own (unique) ones but
  make sure to track provenance with some provided fields:
    - `experiment_id` as structured analysis identifier (e.g. `geo:GSM288124`)
    - `experiment_title` for some colloquial labe (e.g. `sample_03_2nd_run`)
    - `biosample_name` for a local identifier of the biosample in case you use the
      random identifiers from the template (e.g. `005cb7ce-5050-43aa-85ff-cd56ed830535` or `FCL 0089`)
* **use the same `analysis_id` identifiers as in the variants import table**

#### Metadata

Fill in the metadata tables with the relevant data according to best practices etc.
For more information and examples please refer to the
[Beacon documentation](https://docs.genomebeacons.org/model/) and bycon's
[datatable mappings](). Particularly, the bycon version does not provide support for
all Beacon parameters but then also adds additionl fields which mostly support
cancer specific use cases (e.g. `icdo_morphology`, `icdo_topography`) and dedicated
fields for selected external identifiers (e.g. `geo_accession`, `tcga_id`).

Some considerations:

* `biosample_notes` (in Beacon `biosamples.notes`) can e.g. be used for a descriptive
  labeling (e.g. "Serous ovarian tumor [Serous papillary adenocarcinoma, metastasized, G2]")
* time periods (age, followup...) are provided as ISO8601 strings (e.g. `P23Y5M` or `P95D`)

### 3. Format the variants table

Use the provided variants table template to reformat your input data accordingly.

Some considerations:

* the upstream ids (`analysis_id`, `biosample_id`, `individual_id`) have to match the
  ones in the metadata tables
* for `sequence_id` please use the refSeq ids for GRCh38 (e.g. `refseq:NC_000005.10`
instead of `chr5` or such); see `bycon/rsrc/genomes/grch38/refseq_chromosomes.yaml`

...

### 4. Import the data

Importing data requires the existence of all upstream entities. Basically, if one
imports biosamples it is checked if they have values for `individual_id` and then if
these values have existing records. Therefore a complete import sequence when using a
combined `metadata.tsv` file will look like:

1. `importers/individualsInserter.py -d myOwnDatasetName -i wherever/metadata.tsv`
2. `importers/biosamplesInserter.py -d myOwnDatasetName -i wherever/metadata.tsv`
3. `importers/analysisInserter.py -d myOwnDatasetName -i wherever/metadata.tsv`
4. `importers/variantsInserter.py -d myOwnDatasetName -i wherever/variants.tsv`

The `-d` option is used to provide a dataset name (of an existing dataset; see
further information how to get there...).


