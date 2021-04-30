## `byconeer`

The `byconeer` sub-package of `bycon` contains essential utility scripts for the
setup and maintenance of a Progenetix-style Beacon environment.

### Progenetix Update Commands

1. Import / generate `variants`

2. Import / generate `callsets`

3. Process `callsets` & `variants` for statusmaps and CNV statistics

Core data element for the Progenetix environment are the "statusmaps", i.e. the
binned CNV calls (currently im 1Mb bins). The statusmaps are stored inside the
`info` parameter of each callset with a current structure of:

```
...
info:
  statusmaps:
  	dupcoverage: [ 0.023, 1, 1, 1, 1, 0.782, 0, 0, 0, ... ]
  	delcoverage: [ 0, 0, 0, 0, 0.002, 0.703, 0, 0, 0, ... ]
  	dupmax: [ 0.348, 0.348, 0.348, 0.348, 0.348, 0, 0, 0, ...]
  	delmin: [ 0, 0, 0, 0, -0.182, -0.182, 0, 0, 0, ...]
...
```

The maps are generated with the [callsetsRefresher](callsetsRefresher.py)
collecting all variants for each callset & then matching overlaps to the intervals.

```
byconeer/callsetsRefresher.py -d progenetix 
```

This also allows just to add statusmaps and statistics for single series which have beed added / fixed:

```
byconeer/callsetsRefresher.py -d progenetix -t 1 -f "icdom-85002"
```

4. Import / refresh `biosamples`

##### biosamplesInserter

##### biosamplesRefresher

The `biosamplesRefresher.py` script is used for global "data fixes", e.g. the
addition of CNV statistics from callsets or population of attributes from
other collections. This is a utility scriopt hich needs occasional adjustments
depending on the use cases and changing data schemas.

```
byconeer/biosamplesRefresher.py -d progenetix
```

5. Import / refresh `individuals`

6. Generate / refresh `collations`

Due to the possibly nested place of any given code collations can be only
re-created right now and not just updated for individual matches. This may
change...

```
byconeer/collationsCreator.py -d progenetix
```

7. Generate `frequencymaps`

8. Add / refresh publications

9. Rebuild ontologymaps

10. Update the statistics database

```
byconeer/beaconinfoCreator.py
```
