# Bycon Tests

## Using IP and script paths

This is especially useful if one wants to make sure which specific nmachine is being
used, circumvent services like Cloudflare etc.

http://127.0.0.1/cgi-bin/bycon/services/services.py?requestEntityPathId=collationplots&filters=pgx:icdom-85003
http://130.60.62.5/cgi-bin/bycon/services/services.py?requestEntityPathId=collationplots&filters=pgx:icdom-85003
http://127.0.0.1/cgi-bin/bycon/beaconServer/beacon.py?requestEntityPathId=datasets
http://127.0.0.1/cgi-bin/bycon/beaconServer/beacon.py?requestEntityPathId=biosamples&testMode=true


## Standard Beacon Protocol

http://progenetix.test/beacon/biosamples?filters=NCIT:C3697

http://progenetix.test/beacon/biosamples/pgxbs-kftvhyvb/phenopackets

http://progenetix.test/beacon/biosamples?referenceName=refseq:NC_000009.12&variantType=EFO:0030067&start=21000000,21975098&end=21967753,23000000&filters=NCIT:C3058&limit=10

http://progenetix.test/beacon/genomicVariations/?referenceName=NC_000017.11&start=7577120&referenceBases=G&alternateBases=A

http://progenetix.test/beacon/g_variants/pgxvar-5bab576a727983b2e00b8d32

http://progenetix.test/beacon/analyses/?referenceName=17&variantType=DEL&start=5000000&start=7676592&end=7669607&end=10000000&requestedGranularity=count

http://refcnv.test/beacon/biosamples/onekgbs-HG00142/g_variants

## Beacon Requests bwith Additional or Experimental paramaters

http://progenetix.test/beacon/biosamples/?cytoBands=8q24.1&limit=100&variantType=EFO:0030070&filters=NCIT:C4017

http://progenetix.test/beacon/g_variants/?referenceName=8&mateName=12&start=45100000&end=47300000&mateStart=26200000&mateEnd=35600000&variantType=SO:0000806




## Bycon Services


http://progenetix.test/services/collations?id=pgx:icdom-81703

http://progenetix.test/services/collationplots/pgx:icdom-81703

http://progenetix.test/services/pgxsegvariants/pgxbs-kftva59y

http://progenetix.test/services/samplematrix/pgxbs-kftva59y

http://progenetix.test/services/samplematrix?referenceName=17&variantType=DEL&start=5000000&start=7676592&end=7669607&end=10000000&filters=pgx:icdom-81703

http://progenetix.test/services/sampletable?filters=NCIT:C3697

http://progenetix.test/services/sampleplots/pgxbs-kftvkafc/?plotType=samplesplot&plotPars=plot_chros=3,5,6,14



http://progenetix.test/services/ontologymaps?filters=NCIT:C105555


## Not Working

http://progenetix.test/beacon/biosamples?requestedGranularity=count&variantMaxLength=3000000&limit=100&variantType=EFO:0030067&geneId=TP53,CDKN2A&filters=NCIT:C3058

