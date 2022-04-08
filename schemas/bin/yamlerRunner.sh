BASEDIR=$(dirname $0)
BYCONSCHEMAS=$BASEDIR/..

BEACONROOT=/Users/$USER/GitHub/beacon-v2

# initial conversion from separate schemas
BEACONMODELPATH=$BEACONROOT/models/src/beacon-v2-default-model/
BEACONFRAMEWORKPATH=$BEACONROOT/framework/src/

echo "pulling $BEACONROOT"
git -C $BEACONROOT pull


for KIND in src json
do
	mkdir -p $BYCONSCHEMAS/$KIND/beacon-v2-default-model
	mkdir -p $BYCONSCHEMAS/$KIND/framework
done

rsync -rv --exclude=".git*" $BEACONMODELPATH $BYCONSCHEMAS/src/beacon-v2-default-model/
rsync -rv --exclude=".git*" $BEACONFRAMEWORKPATH $BYCONSCHEMAS/src/framework/
# 
# $BASEDIR/beaconYamler.py -i $BEACONMODELPATH -t json -x yaml -o $UNITYPATH/models/src/$BEACONMODELNAME
# $BASEDIR/beaconYamler.py -i $BEACONFRAMEWORKPATH -t json -x yaml -o $UNITYPATH/framework/src
# 
# # recurring conversion from the source files to the exported versions
$BASEDIR/beaconYamler.py -i $BYCONSCHEMAS/src -t yaml -x json -o $BYCONSCHEMAS/json
# $BASEDIR/beaconYamler.py -i $BYCONSCHEMAS/src/beacon-v2-default-model -t yaml -x json -o $BYCONSCHEMAS/json/beacon-v2-default-model
$BASEDIR/beaconYamler.py -i $BYCONSCHEMAS/src/framework -t yaml -x json -o $BYCONSCHEMAS/json/framework
