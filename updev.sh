# This script removes the system bycon, updates locally from the current source
# and then performs the server update.

# We're using versioned pip and python here.
# CAVE: Installation with `--no-isolation` to enable offline builds
pip3 uninstall bycon --break-system-packages
python3 -m build --no-isolation --sdist .

# Temporary installation target; removed at the end
BY=(./dist/*tar.gz)
pip3 install $BY --no-index --no-build-isolation --break-system-packages

# making sure that schema source edits are propagated to JSON
./bycon/schemas/bin/yamlerRunner.sh

# generating some documentation source pages, e.g. for parameters
./markdowner.py

# installation of beacon and services apps into the webserver locations
# this also asks for website generation
./install.py

# cleanup
rm -rf ./build
rm -rf ./dist
rm -rf ./bycon.egg-info
