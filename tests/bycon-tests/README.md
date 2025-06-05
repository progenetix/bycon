# Bruno based API tests

This directory contains tests for the [Bruno](https://docs.usebruno.com/)
offline-first open-source API client.

Bruno can be installed either as a

* an [application](https://docs.usebruno.com/get-started/bruno-basics/download)
    - on a Mac also via [Homebrew](https://brew.sh/): `brew install bruno`
* a command line tool via `npm install -g @usebruno/cli`
	- [documentation](https://docs.usebruno.com/bru-cli/)
* [VS Code extension](https://marketplace.visualstudio.com/items?itemName=bruno.bruno)

## Running the tests

This directory contains a set of tests for the `bycon` API. These tests depend on
providing a test server address value for `BYCONHOST` to construct the Beacon
URLs in the format of e.g. `{{BYCONHOST}}/beacon/biosamples/`. The `BYCONHOST`
parameter is either

* provided as an environment variable e.g. `bru run --env-var BYCONHOST=progenetix.org`
* provided from a pre-defined [./environment](environment) through e.g.
  `bru run --env progenetix.test`