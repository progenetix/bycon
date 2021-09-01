## Content of `bycon/beaconServer/config`

This directory contains the configuration files for the various _homonymous_
Beacon endpoints. They follow the principle of either a homonymous directory
containing several configuration files, or a single (`otherEndpoint.yaml`)
configuration.

```
beaconServer
	|-endpoint.py
 	|-otherEndpoint.py
 	|-...
 	|-config
 		|-endpoint
 		|	|-config.yaml
 		|	|-endpoints.yaml
 		|	|-requestParameters.yaml
 		|
 		|-otherEndpoint.yaml
 		|-...

