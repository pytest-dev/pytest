#!/bin/bash

# this assumes plugins are installed as sister directories

set -e
cd ../pytest-pep8
pytest
cd ../pytest-instafail
pytest 
cd ../pytest-cache
pytest
cd ../pytest-xprocess
pytest
#cd ../pytest-cov
#pytest
cd ../pytest-capturelog
pytest
cd ../pytest-xdist
pytest

