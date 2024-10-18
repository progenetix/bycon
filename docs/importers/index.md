# Importing Data

Importing and updating of data for `bycon` databases is discussed in
this section. The relevant apps can be found in the `importers` directory
in the project's root.

## Importing Records in an Existing Database

### Import Table Formats

Importing new sample data alwaays requires the initial import of
_analysis_ data, _i.e._ at least an experimental identifier which then acts as
a reference for the genomic variants.

The importers are designed to handle a tab-delimited data file
in which the first line contains column headers which have to correspond
to values in the `datatable_definitions.yaml` file. However, it is not necessary to
create separate files for all `analyses` & `biosamples` & `individuala`
entities; the importers will handle the data in a single file
which makes sense when having singular relation 1 individual => 1 biosample => 1 analysis (=> n variants).



==TBD==