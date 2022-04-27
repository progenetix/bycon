# Command line tests

```
./beaconServer/beacon.py --filters "pgx:icdom-81703" --requestedSchema biosample --referenceName 9 --start 10000000,12000000 --end 12500000,15000000 --variantType DEL
```

```
./beaconServer/beacon.py --requestedSchema genomicVariant --referenceName 9 --start 10000000,12000000 --end 12500000,15000000 --variantType DEL --output pgxseg > ~/Desktop/test.pgxseg
```

```
./beaconServer/beacon.py --filters "pgx:icdom-81703" --requestedSchema analysis --referenceName 9 --start 10000000,12000000 --end 12500000,15000000 --variantType DEL --output pgxmatrix > ~/Desktop/test.pgxmatrix
```

```
./beaconServer/beacon.py --filters "NCIT:C3058" --output pgxmatrix > ~/Desktop/NCIT_C3058.pgxmatrix
```

```
./services/cytomapper.py --cytoBands 8q24
./services/cytomapper.py --chroBases "9:0-50000000"
```

```
./services/genespans.py --geneId TP53
./services/genespans.py --geneId TP53 --filterPrecision start
```

```
./services/geolocations.py --city Heidel
./services/geolocations.py --geoDistance 20000 --geoLatitude 47.3 --geoLongitude 8.55
```