"""A setuptools based setup module.
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""
from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
setup(
    package_dir={'':"."},
    packages=find_packages(where=here),
    setup_requires=['setuptools_scm'],
    include_package_data=True,
    package_data={'bycon': ['**/*.yaml', '**/*.txt', '**/*.json']}
)
