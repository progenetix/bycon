<!--podmd-->
## _deliveries_

* a simple app which only provides data deliveries from handover objects
* requires a (locally existing) `accessid` parameter
* optionally limiting the response content by supplying a `deliveryKeys` list
(can be comma-concatenated or multiple times parameter)

##### Examples

Examples here need a locally existing `accessid` parameter. The context of the data
(e.g. "biosamples") is provided from the retrieved data object itself and not
apparent from the request.

* <http://progenetix.org/services/deliveries?accessid=003d0488-0b79-4ffa-a38f-2fb932480eee&deliveryKeys=id,biocharacteristics>

The response in this example was a `biosamples` dataset (excerpt):

```json
{
    "response": {
        "results": [
            {
                "id": "PGX_AM_BS_20164920_SM-11YB",
                "biocharacteristics": [
                    {
                        "description": "non-small cell lung carcinoma [cell line H23]",
                        "id": "icdot-C34.9",
                        "label": "lung and bronchus"

    }]}]},
 
    "errors": [],
    "parameters": {
        "accessid": "003d0488-0b79-4ffa-a38f-2fb932480eee",
        "collection": "biosamples",
        "datasetId": "progenetix"
    },
    "warnings": []
}
```

<!--/podmd-->
