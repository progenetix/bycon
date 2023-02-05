"""A setuptools based setup module.
See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="bycon",
    version="1.0.11",
    description="A Python-based environment for the Beacon v2 genomics API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/progenetix/bycon",
    author="Michael Baudis",
    author_email="contact@progenetix.org",
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication",
        "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only"
    ],
    keywords="genomics, Beacon",
    package_dir={'':"."},
    packages=find_packages(where="."),  # Required
    setup_requires=['setuptools_scm'],
    include_package_data=True,
    package_data={'bycon': ['**/*.yaml', '**/*.txt', '**/*.json']},
    python_requires=">=3.7, <4",
    # This field lists other packages that your project depends on to run.
    # Any package you put here will be installed by pip when your project is
    # installed, so they must be valid existing projects.
    #
    # For an analysis of "install_requires" vs pip's requirements files see:
    # https://packaging.python.org/discussions/install-requires-vs-requirements/
    install_requires=["base36", "isodate", "json_ref_dict", "liftover", "numpy", "progress", "pyhumps", "pymongo", "PyYAML", "ruamel.base"],  # Optional
    # Entry points. The following would provide a command called `sample` which
    # executes the function `main` from this package when invoked:
    # entry_points={  # Optional
    #     "console_scripts": [
    #         "sample=sample:main",
    #     ],
    # },
    # List additional URLs that are relevant to your project as a dict.
    #
    project_urls={  # Optional
        "Bug Reports": "https://github.com/progenetix/bycon/issues",
        "Source": "https://github.com/progenetix/bycon/",
    },
)