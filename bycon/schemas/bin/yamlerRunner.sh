BASEDIR=$(dirname $0)
BYCONSCHEMAS=$BASEDIR/..


# initial conversion from separate schemas
# BEACONROOT=/Users/$USER/GitHub/beacon-v2
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
echo "==> converting $BYCONSCHEMAS/bycon-framework-additions/src"
$BASEDIR/beaconYamler.py -i $BYCONSCHEMAS/bycon-framework-additions/src -t yaml -x json -o $BYCONSCHEMAS/bycon-framework-additions/json
