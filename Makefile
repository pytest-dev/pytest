# Set of targets useful for development/release process
PYTHON = python2.7
PATH := $(PWD)/.env/bin:$(PATH)
REGENDOC_ARGS := \
	--normalize "/={8,} (.*) ={8,}/======= \1 ========/" \
	--normalize "/_{8,} (.*) _{8,}/_______ \1 ________/" \
	--normalize "/in \d+.\d+ seconds/in 0.12 seconds/" \
	--normalize "@/tmp/pytest-\d+/@/tmp/pytest-NaN/@"

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
	find doc/en -name '*.rst' -not -path 'doc/en/_build/*' | xargs .env/bin/regendoc ${REGENDOC_ARGS}
	cd doc/en; make html

# upload documentation
upload-docs: develop
	find doc/en -name '*.rst' -not -path 'doc/en/_build/*' | xargs .env/bin/regendoc ${REGENDOC_ARGS} --update
	#cd doc/en; make install

