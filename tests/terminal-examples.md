# Command line tests

```
curl --json @PUT-individuals-from-NCIT-filters.json  "http://progenetix.org/beacon/individuals/"
curl --json @PUT-variants-for-TP53-CDKN2A-DEL-multivars-gliomas.json  "http://progenetix.test/beacon/g_variants/"
curl --json @PUT-variants-for-TP53-allele-DEL-multivars-gliomas.json  "http://progenetix.test/beacon/g_variants/"
curl --json @PUT-variants-for-CDKN2A-DEL-gliomas.json  "http://progenetix.test/beacon/g_variants/"
```

### Standard GET

One might need to URLencode things like `#` ==> `%23`:

```
curl "https://progenetix.org/services/collationplots/?filters=NCIT:C9245,NCIT:C9331,NCIT:C4013&plotPars=plot_axis_y_max=75::plot_area_color=%23ccffdd::plot_gene_symbols=ESR1,MYC,CCND1,ERBB2,TP53::plotChros=1,3,5,6,8,11,13,16,17::plot_width=1200&datasetIds=progenetix" > /Users/$USER/Desktop/histoplot-NCIT_C9245,NCIT_C9331,NCIT_C4013_from-curl.svg
```

The same on a local machine run from `../bycon`:

```
/byconServices/services.py --requestEntityPathId collationplots --filters "NCIT:C9245,NCIT:C9331,NCIT:C4013" --plotPars "plot_axis_y_max=75::plot_area_color=#ccffdd::plot_gene_symbols=ESR1,MYC,CCND1,ERBB2,TP53::plotChros=1,3,5,6,8,11,13,16,17::plot_width=1200" -d progenetix > /Users/$USER/Desktop/histoplot-NCIT_C9245,NCIT_C9331,NCIT_C4013.svg
```

#### Stringified `multivars` Test

```
curl --json '{"meta":{"apiVersion":"2.1"},"query":{"requestParameters":{"variant_multi_pars":[{"referenceName":"refseq:NC_000017.11","start":[7620000],"end":[7680000],"alternateBases":"A"},{"referenceName":"refseq:NC_000017.11","start":[6000000,7687480],"end":[7668422,8000000],"variantType":"EFO:0030067"}]},"filters":[],"requestedGranularity":"record","pagination":{"skip":0,"limit":5}}, "includeHandovers": false}' 'http://progenetix.org/beacon/g_variants/'
```