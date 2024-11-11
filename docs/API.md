# API: Beacon Responses

The following is a list of standard Beacon responses supported by the `bycon` package.
Responses for individual entities or endpoints are grouped by their Beacon framework
response classes (e.g. `beaconResultsetsResponse` for `biosamples`, `g_variants` etc.).\n\n
Please be reminded about the general syntax used in Beacon: A **path element** such
as `/biosamples` corresponds to an entity (here `biosample`). Below these relations
are indicated by the `@` symbol.\n\n

!!! info "API Parameters"
    A complete list of parameters accepted by the API is provided on the [_Web and Command Line Parameters_](API-parameters.md) page.

#### Schemas **{S}**, Tests **{T}** and Examples **{E}**
Tests, examples and schemas are run from the server defined in this site's build instructions
(see the `reference_server_url` entry in `mkdocs.yaml` file in the repository's root).

{%
    include-markdown "generated/beacon-responses.md"
%}

