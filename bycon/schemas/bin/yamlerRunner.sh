BASEDIR=$(dirname $0)
BYCONSCHEMAS=$BASEDIR/..

BEACONROOT=/Users/$USER/GitHub/beacon-v2

# initial conversion from separate schemas
# BEACONMODELPATH=$BEACONROOT/models/src/
# BEACONFRAMEWORKPATH=$BEACONROOT/framework/src/

# echo "pulling $BEACONROOT"
# git -C $BEACONROOT pull
# 
# # recurring conversion from the source files to the exported versions
echo "==> converting $BYCONSCHEMAS/models/src"
$BASEDIR/beaconYamler.py -i $BYCONSCHEMAS/models/src -t yaml -x json -o $BYCONSCHEMAS/models/json
echo "==> converting $BYCONSCHEMAS/framework/src"
$BASEDIR/beaconYamler.py -i $BYCONSCHEMAS/framework/src -t yaml -x json -o $BYCONSCHEMAS/framework/json
