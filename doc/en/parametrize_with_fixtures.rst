=========================
Parametrize with fixtures
=========================

Problem
-------

As a user I have functional tests that I would like to run against various
scenarios.

In this particular example we want to generate a new project based on a
cookiecutter template. We want to test default values but also data that
emulates user input.

- use default values
- emulate user input
  - specify 'author'
  - specify 'project_slug'
  - specify 'author' and 'project_slug'

This is how a functional test could look like:

.. code-block:: python

    import pytest

    @pytest.fixture
    def default_context():
        return {'extra_context': {}}


    @pytest.fixture(params=[
        {'author': 'alice'},
        {'project_slug': 'helloworld'},
        {'author': 'bob', 'project_slug': 'foobar'},
    ])
    def extra_context(request):
        return {'extra_context': request.param}


    @pytest.fixture(params=['default', 'extra'])
    def context(request):
        if request.param == 'default':
            return request.getfuncargvalue('default_context')
        else:
            return request.getfuncargvalue('extra_context')


    def test_generate_project(cookies, context):
        """Call the cookiecutter API to generate a new project from a
        template.
        """
        result = cookies.bake(extra_context=context)

        assert result.exit_code == 0
        assert result.exception is None
        assert result.project.isdir()


Issues
------

* By using ``request.getfuncargvalue()`` we rely on actual fixture function
  execution to know what fixtures are involved, due to it's dynamic nature
* More importantly, ``request.getfuncargvalue()`` cannot be combined with
  parametrized fixtures, such as ``extra_context``
* This is very inconvenient if you wish to extend an existing test suite by
  certain parameters for fixtures that are already used by tests

pytest version 3.0 and higher reports an error if you try to run above code::

    Failed: The requested fixture has no parameter defined for the current
    test.

    Requested fixture 'extra_context'

