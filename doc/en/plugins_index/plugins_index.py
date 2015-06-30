"""
Script to generate the file `index.txt` with information about
pytest plugins taken directly from PyPI.

Usage:
    python plugins_index.py

This command will update `index.txt` in the same directory found as this script.
This should be issued before every major documentation release to obtain latest
versions from PyPI.

Also includes plugin compatibility between different python and pytest versions,
obtained from http://plugincompat.herokuapp.com.
"""
from __future__ import print_function
from collections import namedtuple
import datetime
from distutils.version import LooseVersion
import itertools
from optparse import OptionParser
import os
import sys
import pytest


def get_proxy(url):
    """
    wrapper function to obtain a xmlrpc proxy, taking in account import
    differences between python 2.X and 3.X

    :param url: url to bind the proxy to
    :return: a ServerProxy instance
    """
    if sys.version_info < (3, 0):
        from xmlrpclib import ServerProxy
    else:
        from xmlrpc.client import ServerProxy
    return ServerProxy(url)


def iter_plugins(client):
    """
    Returns an iterator of (name, version) from PyPI.

    :param client: ServerProxy
    :param search: package names to search for
    """
    for plug_data in client.search({'name': 'pytest'}):
        if plug_data['name'].startswith('pytest-'):
            yield plug_data['name'], plug_data['version']


def get_latest_versions(plugins):
    """
    Returns an iterator of (name, version) from the given list of (name,
    version), but returning only the latest version of the package. Uses
    distutils.LooseVersion to ensure compatibility with PEP386.
    """
    plugins = [(name, LooseVersion(version)) for (name, version) in plugins]
    for name, grouped_plugins in itertools.groupby(plugins, key=lambda x: x[0]):
        name, loose_version = list(grouped_plugins)[-1]
        yield name, str(loose_version)


def obtain_plugins_table(plugins, client, verbose, pytest_ver):
    """
    Returns information to populate a table of plugins, their versions,
    authors, etc.

    The returned information is a list of columns of `ColumnData`
    namedtuples(text, link). Link can be None if the text for that column
    should not be linked to anything.

    :param plugins: list of (name, version)
    :param client: ServerProxy
    :param verbose: print plugin name and version as they are fetch
    :param pytest_ver: pytest version to use.
    """
    if pytest_ver is None:
        pytest_ver = pytest.__version__

    def get_repo_markup(repo):
        """
        obtains appropriate markup for the given repository, as two lines
        that should be output in the same table row. We use this to display an icon
        for known repository hosts (github, etc), just a "?" char when
        repository is not registered in pypi or a simple link otherwise.
        """
        target = repo
        if 'github.com' in repo:
            image = 'github.png'
        elif 'bitbucket.org' in repo:
            image = 'bitbucket.png'
        elif repo.lower() == 'unknown':
            return '?', ''
        else:
            image = None

        if image is not None:
            image_markup = '.. image:: %s' % image
            target_markup = '   :target: %s' % repo
            pad_right = ('%-' + str(len(target_markup)) + 's')
            return pad_right % image_markup, target_markup
        else:
            return ('`link <%s>`_' % target), ''
    
    def sanitize_summary(summary):
        """Make sure summaries don't break our table formatting.
        """
        return summary.replace('\n', ' ')

    rows = []
    ColumnData = namedtuple('ColumnData', 'text link')
    headers = ['Name', 'Py27', 'Py34', 'Home', 'Summary']
    repositories = obtain_override_repositories()
    print('Generating plugins_index page (pytest-{0})'.format(pytest_ver))
    plugins = list(plugins)
    for index, (package_name, version) in enumerate(plugins):
        if verbose:
            print(package_name, version, '...', end='')

        release_data = client.release_data(package_name, version)

        common_params = dict(
            site='http://plugincompat.herokuapp.com',
            name=package_name,
            version=version)

        repository = repositories.get(package_name, release_data['home_page'])
        repo_markup_1, repo_markup_2 = get_repo_markup(repository)

        # first row: name, images and simple links
        url = '.. image:: {site}/status/{name}-latest'
        image_url = url.format(**common_params)
        image_url += '?py={py}&pytest={pytest}'
        row = (
            ColumnData(package_name, release_data['package_url']),
            ColumnData(image_url.format(py='py27', pytest=pytest_ver),
                       None),
            ColumnData(image_url.format(py='py34', pytest=pytest_ver),
                       None),
            ColumnData(
                repo_markup_1,
                None),
            ColumnData(sanitize_summary(release_data['summary']), None),
        )
        assert len(row) == len(headers)
        rows.append(row)

        # second row: links for images (they should be in their own line)
        url = '    :target: {site}/output/{name}-latest'
        output_url = url.format(**common_params)
        output_url += '?py={py}&pytest={pytest}'

        row = (
            ColumnData('', None),
            ColumnData(output_url.format(py='py27', pytest=pytest_ver),
                       None),
            ColumnData(output_url.format(py='py34', pytest=pytest_ver),
                       None),
            ColumnData(repo_markup_2, None),
            ColumnData('', None),

        )
        assert len(row) == len(headers)
        rows.append(row)

        if verbose:
            print('OK (%d%%)' % ((index + 1) * 100 / len(plugins)))

    print('Done: %d plugins' % len(plugins))

    return headers, rows


def obtain_override_repositories():
    """
    Used to override the "home_page" obtained from pypi to known
    package repositories. Used when the author didn't fill the "home_page"
    field in setup.py.

    :return: dict of {package_name: repository_url}
    """
    return {
        'pytest-blockage': 'https://github.com/rob-b/pytest-blockage',
        'pytest-konira': 'http://github.com/alfredodeza/pytest-konira',
        'pytest-sugar': 'https://github.com/Frozenball/pytest-sugar',
    }


def generate_plugins_index_from_table(filename, headers, rows, pytest_ver):
    """
    Generates a RST file with the table data given.

    :param filename: output filename
    :param headers: see `obtain_plugins_table`
    :param rows: see `obtain_plugins_table`
    :param pytest_ver: see `obtain_plugins_table`
    """
    # creates a list of rows, each being a str containing appropriate column
    # text and link
    table_texts = []
    for row in rows:
        column_texts = []
        for i, col_data in enumerate(row):
            text = '`%s <%s>`_' % (
                col_data.text,
                col_data.link) if col_data.link else col_data.text
            column_texts.append(text)
        table_texts.append(column_texts)

    # compute max length of each column so we can build the rst table
    column_lengths = [len(x) for x in headers]
    for column_texts in table_texts:
        for i, row_text in enumerate(column_texts):
            column_lengths[i] = max(column_lengths[i], len(row_text) + 2)

    def get_row_limiter(char):
        return ' '.join(char * length for length in column_lengths)

    with open(filename, 'w') as f:
        # header
        print(HEADER, file=f)
        print(file=f)

        # table
        print(get_row_limiter('='), file=f)
        formatted_headers = [
            '{0:^{fill}}'.format(header, fill=column_lengths[i])
            for i, header in enumerate(headers)]
        print(*formatted_headers, file=f)
        print(get_row_limiter('='), file=f)

        for column_texts in table_texts:
            formatted_rows = [
                '{0:^{fill}}'.format(row_text, fill=column_lengths[i])
                for i, row_text in enumerate(column_texts)
            ]
            print(*formatted_rows, file=f)
        print(file=f)
        print(get_row_limiter('='), file=f)
        print(file=f)
        today = datetime.date.today().strftime('%Y-%m-%d')
        print('*(Updated on %s)*' % today, file=f)


def generate_plugins_index(client, filename, verbose, pytest_ver):
    """
    Generates an RST file with a table of the latest pytest plugins found in
    PyPI.

    :param client: ServerProxy
    :param filename: output filename
    :param verbose: print name and version of each plugin as they are fetch
    :param pytest_ver: pytest version to use; if not given, use current pytest
        version.
    """
    plugins = get_latest_versions(iter_plugins(client))
    headers, rows = obtain_plugins_table(plugins, client, verbose, pytest_ver)
    generate_plugins_index_from_table(filename, headers, rows, pytest_ver)


def main(argv):
    """
    Script entry point. Configures an option parser and calls the appropriate
    internal function.
    """
    filename = os.path.join(os.path.dirname(__file__), 'index.txt')
    url = 'http://pypi.python.org/pypi'

    parser = OptionParser(
        description='Generates a restructured document of pytest plugins from PyPI')
    parser.add_option('-f', '--filename', default=filename,
                      help='output filename [default: %default]')
    parser.add_option('-u', '--url', default=url,
                      help='url of PyPI server to obtain data from [default: %default]')
    parser.add_option('-v', '--verbose', default=False, action='store_true',
                      help='verbose output')
    parser.add_option('--pytest-ver', default=None, action='store',
                      help='generate index for this pytest version (default current version)')
    (options, _) = parser.parse_args(argv[1:])

    client = get_proxy(options.url)
    generate_plugins_index(client, options.filename, options.verbose, options.pytest_ver)

    print()
    print('%s updated.' % options.filename)
    return 0


# header for the plugins_index page
HEADER = '''.. _plugins_index:

List of Third-Party Plugins
===========================

The table below contains a listing of plugins found in PyPI and
their status when tested when using latest py.test and python versions.

A complete listing can also be found at
`plugincompat <http://plugincompat.herokuapp.com/>`_, which contains tests
status against other py.test releases.
'''


if __name__ == '__main__':
    sys.exit(main(sys.argv))
