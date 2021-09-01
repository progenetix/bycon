BYCONPATH=~/groupbox/dbtools/bycon
BYCONRSRCPATH=~/groupbox/dbtools/bycon/beaconServer/rsrc
BEACONMODELPATH=~/GitHub/ga4gh-beacon/beacon-v2-Models/BEACON-V2-draft4-Model
BEACONFRAMEWORKPATH=~/GitHub/ga4gh-beacon/beacon-framework-v2

cd $BYCONPATH/byconeer/
./yamler.py -i $BEACONMODELPATH -t json -o $BYCONRSRCPATH/beacon-v2-dev/model
./yamler.py -i $BEACONFRAMEWORKPATH -t json -o $BYCONRSRCPATH/beacon-v2-dev/framework
