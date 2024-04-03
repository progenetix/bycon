# This script removes the system bycon, updates locally from the current source
# and then performs the server update.

pip3 uninstall bycon
rm -rf ./dist
rm ./bycon/beaconServer/local/*.*
python3 -m build --sdist .
BY=(./dist/*tar.gz)
pip3 install $BY
# pipreqs --force .
# python3 -m build --wheel && twine upload dist/*
# git tag v1.6.3  & git push --tags
./install.py
# TODO: the caller for this should beexternal
../byconaut/install.py
