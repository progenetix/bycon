# This script removes the system bycon, updates locally from the current source
# and then performs the server update.

pip3 uninstall bycon --break-system-packages
rm -rf ./dist
rm ./bycon/beaconServer/local/*.*
python3 -m build --sdist .
BY=(./dist/*tar.gz)
pip3 install $BY --break-system-packages
# pipreqs --force .
# python3 -m build --wheel && twine upload dist/*
# git tag v1.8.4  & git push --tags
./install.py
# TODO: the caller for this should be external
../byconaut/install.py
rm -rf ./build
rm -rf ./dist
rm -rf ./bycon.egg-info
