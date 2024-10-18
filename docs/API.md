# API Documentation

## Parameters  [... more](/generated/argument_definitions)

The `bycon` package supports number of parameters for filtering and querying the data which includes and extends
standard Beacon parameters and can - depending on the parameter and the current scope - in general be
invoked through HTTP requests and as command line arguments.

Only parameters sefined in `config/argument_definitions.yaml` will be
interpreted. Those parameters are listed in [this document](/generated/argument_definitions).

## Beacon Endpoints

==TBD==

## Service Endpoints [... more](/generated/services)

==TBD==

## Endpoint Tests [... more](/tests)

==TBD==

## Plotting [... more](/plotting)

The `byconServices` package inside `bycon` provides a number of plotting functions which can be used to visualize the data in the database. Generally
plot functionality is focussed on generating CNV visualizations for per-sample and
aggregated (e.g. frequencyplots). Detailed information with use cases as well as plot parameter documentation can be found on [this page](/plotting).