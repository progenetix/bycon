BASEDIR=$(dirname $0)
BYCONSCHEMAS=$BASEDIR/..

BEACONROOT=/Users/$USER/GitHub/beacon-v2

# initial conversion from separate schemas
# BEACONMODELPATH=$BEACONROOT/models/src/
# BEACONFRAMEWORKPATH=$BEACONROOT/framework/src/

# echo "pulling $BEACONROOT"
# git -C $BEACONROOT pull


# for KIND in src json
# do
# 	mkdir -p $BYCONSCHEMAS/$KIND/beacon-v2-default-model
# 	mkdir -p $BYCONSCHEMAS/$KIND/framework
# done

# rsync -rv --exclude=".git*" --delete $BEACONMODELPATH $BYCONSCHEMAS/src/beacon-v2-default-model/
# rsync -rv --exclude=".git*" --delete $BEACONFRAMEWORKPATH $BYCONSCHEMAS/src/framework/
# 
# $BASEDIR/beaconYamler.py -i $BEACONMODELPATH -t json -x yaml -o $UNITYPATH/models/src/$BEACONMODELNAME
# $BASEDIR/beaconYamler.py -i $BEACONFRAMEWORKPATH -t json -x yaml -o $UNITYPATH/framework/src
# 
# # recurring conversion from the source files to the exported versions
echo "==> converting $BYCONSCHEMAS/models/src"
$BASEDIR/beaconYamler.py -i $BYCONSCHEMAS/models/src -t yaml -x json -o $BYCONSCHEMAS/models/json
echo "==> converting $BYCONSCHEMAS/framework/src"
$BASEDIR/beaconYamler.py -i $BYCONSCHEMAS/framework/src -t yaml -x json -o $BYCONSCHEMAS/framework/json
