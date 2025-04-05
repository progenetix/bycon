# This script removes the system bycon, updates locally from the current source
# and then performs the server update.

pip3 uninstall bycon --break-system-packages
python3 -m build --sdist .
BY=(./dist/*tar.gz)
pip3 install $BY --break-system-packages
./bycon/schemas/bin/yamlerRunner.sh
./markdowner.py
# pipreqs --force .
# python3 -m build --wheel && twine upload dist/*
./install.py
rm -rf ./build
rm -rf ./dist
rm -rf ./bycon.egg-info
# rsync -avh --exclude=logs --exclude=.git ./ ~/Github/bycon/
# git tag v2.2.6  & git push --tags
