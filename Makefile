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
	find doc/en -name '*.txt' -not -path 'doc/en/_build/*' | xargs .env/bin/regendoc
	cd doc/en; make html

# upload documentation
upload-docs: develop
	find doc/en -name '*.txt' -not -path 'doc/en/_build/*' | xargs .env/bin/regendoc --update
	cd doc/en; make install
