# API: Web and Command Line Parameters

## General API Parameters

The `bycon` package supports number of parameters for filtering and querying the data which includes and extends
standard Beacon parameters and can - depending on the parameter and the current scope - in general be
invoked through HTTP requests and as command line arguments.

Only parameters defined in `config/argument_definitions.yaml` will be
interpreted.

Parameters are listed in `snake_case` format although for command line arguments
(and also optionally web requests) `camelCase` versions are required (see the `cmdFlags`).


{%
    include-markdown "generated/argument_definitions.md"
%}

## Services: Plot Parameters

The `byconServices` package inside `bycon` provides a number of plotting functions which can be used to visualize the data in the database. Generally
plot functionality is focussed on generating CNV visualizations for per-sample and
aggregated CNV data (e.g. frequencyplots). Additionally some geographic map projectins are provided e.g. for samples and metadata.

More information can be found on these pages:

* plot documentation on [this page](plotting.md)

{%
    include-markdown "generated/plot_defaults.md"
%}
