# API Documentation

{%
    include-markdown "generated/beacon-responses.md"
%}

## Service Endpoints [:link:](/generated/services.md)

Additionally to the standard Beacon endpoints provided for the Beacon framework and default data model
`bycon` also has a number of service endpoints. Some of them are used to provide direct Beacon support (e.g. `/endpoints` or `/schemas` to implement endpoints accessed from Beacon responses), while others
provide more specialized functionality (e.g. `/cytomapper`).

More information:

* [list of bycon services](/generated/services.md)

## Parameters  [... more](/generated/argument_definitions.md)

The `bycon` package supports number of parameters for filtering and querying the data which includes and extends
standard Beacon parameters and can - depending on the parameter and the current scope - in general be
invoked through HTTP requests and as command line arguments.

Only parameters sefined in `config/argument_definitions.yaml` will be
interpreted. Those parameters are listed in [this document](/generated/argument_definitions).

## Endpoint Tests [... more](/tests.md)

==TBD==

## Plotting

The `byconServices` package inside `bycon` provides a number of plotting functions which can be used to visualize the data in the database. Generally
plot functionality is focussed on generating CNV visualizations for per-sample and
aggregated CNV data (e.g. frequencyplots). Additionally some geographic map projectins are provided e.g. for samples and metadata.

More information can be found on these pages:

* plot documentation on [this page](./plotting.md)
* plot [parameters and defaults](./generated/plot_defaults.md)
