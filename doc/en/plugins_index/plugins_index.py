'''
Script to generate the file `plugins_index.txt` with information about pytest plugins taken directly 
from a live PyPI server.

This will evolve to include test compatibility (pythons and pytest versions) information also.
'''
from collections import namedtuple
import datetime
from distutils.version import LooseVersion
import itertools
from optparse import OptionParser
import os
import sys
import xmlrpclib

import pytest

#===================================================================================================
# iter_plugins
#===================================================================================================
def iter_plugins(client, search='pytest-'):
    '''
    Returns an iterator of (name, version) from PyPI.
    
    :param client: xmlrpclib.ServerProxy
    :param search: package names to search for 
    '''
    for plug_data in client.search({'name' : search}):
        yield plug_data['name'], plug_data['version']


#===================================================================================================
# get_latest_versions
#===================================================================================================
def get_latest_versions(plugins):
    '''
    Returns an iterator of (name, version) from the given list of (name, version), but returning 
    only the latest version of the package. Uses distutils.LooseVersion to ensure compatibility
    with PEP386.
    '''
    plugins = [(name, LooseVersion(version)) for (name, version) in plugins]
    for name, grouped_plugins in itertools.groupby(plugins, key=lambda x: x[0]):
        name, loose_version = list(grouped_plugins)[-1]
        yield name, str(loose_version)
        
        
#===================================================================================================
# obtain_plugins_table
#===================================================================================================
def obtain_plugins_table(plugins, client):    
    '''
    Returns information to populate a table of plugins, their versions, authors, etc.
    
    The returned information is a list of columns of `ColumnData` namedtuples(text, link). Link
    can be None if the text for that column should not be linked to anything. 
    
    :param plugins: list of (name, version)
    :param client: xmlrpclib.ServerProxy
    '''
    rows = []
    ColumnData = namedtuple('ColumnData', 'text link')
    headers = ['Name', 'Author', 'Downloads', 'Python 2.7', 'Python 3.3', 'Summary']
    pytest_version = pytest.__version__
    print '*** pytest-{0} ***'.format(pytest_version)
    plugins = list(plugins)
    for index, (package_name, version) in enumerate(plugins):
        print package_name, version, '...',
        
        release_data = client.release_data(package_name, version)
        download_count = release_data['downloads']['last_month']
        image_url = '.. image:: http://pytest-plugs.herokuapp.com/status/{name}-{version}'.format(name=package_name,
                                                                                                  version=version)
        image_url += '?py={py}&pytest={pytest}'
        row = (
            ColumnData(package_name + '-' + version, release_data['release_url']),
            ColumnData(release_data['author'], release_data['author_email']),
            ColumnData(str(download_count), None),
            ColumnData(image_url.format(py='py27', pytest=pytest_version), None),
            ColumnData(image_url.format(py='py33', pytest=pytest_version), None),
            ColumnData(release_data['summary'], None),
        )
        assert len(row) == len(headers)
        rows.append(row)
        
        print 'OK (%d%%)' % ((index + 1) * 100 / len(plugins)) 
        
    return headers, rows    


#===================================================================================================
# generate_plugins_index_from_table
#===================================================================================================
def generate_plugins_index_from_table(filename, headers, rows):
    '''
    Generates a RST file with the table data given.
     
    :param filename: output filename
    :param headers: see `obtain_plugins_table`
    :param rows: see `obtain_plugins_table`
    '''
    # creates a list of rows, each being a str containing appropriate column text and link
    table_texts = []
    for row in rows:
        column_texts = []
        for i, col_data in enumerate(row): 
            text = '`%s <%s>`_' % (col_data.text, col_data.link) if col_data.link else col_data.text
            column_texts.append(text)
        table_texts.append(column_texts)
        
    # compute max length of each column so we can build the rst table
    column_lengths = [len(x) for x in headers]
    for column_texts in table_texts:
        for i, row_text in enumerate(column_texts):
            column_lengths[i] = max(column_lengths[i], len(row_text) + 2)
    
    def get_row_limiter(char):
        return ' '.join(char * length for length in column_lengths)
    
    with file(filename, 'w') as f:
        # write welcome 
        print >> f, '.. _plugins_index:'
        print >> f
        print >> f, 'List of Third-Party Plugins'
        print >> f, '==========================='
        print >> f
        
        # table 
        print >> f, get_row_limiter('=')
        for i, header in enumerate(headers):
            print >> f, '{0:^{fill}}'.format(header, fill=column_lengths[i]),
        print >> f
        print >> f, get_row_limiter('=')
        
        for column_texts in table_texts:
            for i, row_text in enumerate(column_texts):
                print >> f, '{0:^{fill}}'.format(row_text, fill=column_lengths[i]),
            print >> f
        print >> f
        print >> f, get_row_limiter('=')
        print >> f
        print >> f, '*(Downloads are given from last month only)*'
        print >> f
        print >> f, '*(Updated on %s)*' % _get_today_as_str()
        

#===================================================================================================
# _get_today_as_str
#===================================================================================================
def _get_today_as_str():
    '''
    internal. only exists so we can patch it in testing.
    '''
    return datetime.date.today().strftime('%Y-%m-%d')


#===================================================================================================
# generate_plugins_index
#===================================================================================================
def generate_plugins_index(client, filename):
    '''
    Generates an RST file with a table of the latest pytest plugins found in PyPI. 
    
    :param client: xmlrpclib.ServerProxy
    :param filename: output filename
    '''
    plugins = get_latest_versions(iter_plugins(client))
    headers, rows = obtain_plugins_table(plugins, client)
    generate_plugins_index_from_table(filename, headers, rows)
    

#===================================================================================================
# main
#===================================================================================================
def main(argv):
    filename = os.path.join(os.path.dirname(__file__), 'plugins_index.txt')
    url = 'http://pypi.python.org/pypi'
    
    parser = OptionParser(description='Generates a restructured document of pytest plugins from PyPI')
    parser.add_option('-f', '--filename', default=filename, help='output filename [default: %default]')
    parser.add_option('-u', '--url', default=url, help='url of PyPI server to obtain data from [default: %default]')
    (options, _) = parser.parse_args(argv[1:])

    client = xmlrpclib.ServerProxy(options.url)
    generate_plugins_index(client, options.filename)
    
    print
    print '%s Updated.' % options.filename
    return 0

#===================================================================================================
# main
#===================================================================================================
if __name__ == '__main__':
    sys.exit(main(sys.argv))
