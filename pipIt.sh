pipreqs --force .
python3 -m build --wheel && twine upload dist/*
rm -rf ./build
rm -rf ./dist
rm -rf ./bycon.egg-info
