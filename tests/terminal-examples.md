# Command line tests

```
curl --json @PUT-individuals-from-NCIT-filters.json  "http://progenetix.org/beacon/individuals/"
curl --json @PUT-variants-for-TP53-CDKN2A-DEL-multivars-gliomas.json  "http://progenetix.test/beacon/g_variants/"
curl --json @PUT-variants-for-TP53-allele-DEL-multivars-gliomas.json  "http://progenetix.test/beacon/g_variants/"
curl --json @PUT-variants-for-CDKN2A-DEL-gliomas.json  "http://progenetix.test/beacon/g_variants/"
```

#### Stringified `multivars` Test

```
curl --json '{"meta":{"apiVersion":"2.1"},"query":{"requestParameters":{"variant_multi_pars":[{"referenceName":"refseq:NC_000017.11","start":[7620000],"end":[7680000],"alternateBases":"A"},{"referenceName":"refseq:NC_000017.11","start":[6000000,7687480],"end":[7668422,8000000],"variantType":"EFO:0030067"}]},"filters":[]},"requestedGranularity":"record","pagination":{"skip":0,"limit":5}, "includeHandovers": false}' 'http://progenetix.org/beacon/g_variants/'
```