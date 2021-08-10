BYCONPATH=~/groupbox/dbtools/bycon
BEACONMODELPATH=~/GitHub/ga4gh-beacon/beacon-v2-Models/BEACON-V2-draft4-Model
BEACONFRAMEWORKPATH=~/GitHub/ga4gh-beacon/beacon-framework-v2

cd $BYCONPATH/byconeer/
./yamler.py -i $BEACONMODELPATH -t json -o $BYCONPATH/beaconServer/model
./yamler.py -i $BEACONFRAMEWORKPATH -t json -o $BYCONPATH/beaconServer/framework
