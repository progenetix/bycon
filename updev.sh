# This script removes the system bycon, updates locally from the current source
# and then performs the server update.

pip3 uninstall bycon
rm -rf ./dist
rm ./bycon/beaconServer/local/*.*
python3 -m build --sdist .
BY=(./dist/*tar.gz)
pip install $BY
# python3 -m build --wheel && twine upload dist/*
./install.py
../byconaut/install.py
