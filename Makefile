# Set of targets useful for development/release process
PYTHON = python2.7
PATH := $(PWD)/.env/bin:$(PATH)

# prepare virtual python environment
.env:
	virtualenv .env -p $(PYTHON)

# install all needed for development
develop: .env
	pip install -e . tox -r requirements-docs.txt

# clean the development envrironment
clean:
	-rm -rf .env

# generate documentation
docs: develop
	cd doc/en; make html
	find doc/en/ -name '*.txt' | xargs .env/bin/regendoc

# upload documentation
upload-docs: develop
	cd doc/en; make install
