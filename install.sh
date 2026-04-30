python3 -m build --no-isolation --sdist .
BY=(./dist/bycon*tar.gz)
pip3 install $BY --no-index --no-build-isolation --break-system-packages
rm -rf ./build                           
rm -rf ./dist
rm -rf ./bycon.egg-info