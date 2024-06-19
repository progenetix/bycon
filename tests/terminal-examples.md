# Command line tests

```
curl --json @PUT-individuals-from-NCIT-filters.json  "http://progenetix.org/beacon/individuals/"
curl --json @PUT-variants-for-TP53-CDKN2A-DEL-multivars-gliomas.json  "http://progenetix.test/beacon/g_variants/"
curl --json @PUT-variants-for-TP53-allele-DEL-multivars-gliomas.json  "http://progenetix.test/beacon/g_variants/"
curl --json @PUT-variants-for-CDKN2A-DEL-gliomas.json  "http://progenetix.test/beacon/g_variants/"
```