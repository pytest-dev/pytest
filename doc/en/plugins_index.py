from collections import namedtuple
from distutils.version import LooseVersion
import itertools
import os
import sys
import xmlrpclib


#===================================================================================================
# iter_pypi_plugins
#===================================================================================================
def iter_pypi_plugins(client):
    for plug_data in client.search({'name' : 'pytest-'}):
        yield plug_data['name'], plug_data['version']


#===================================================================================================
# get_latest_versions
#===================================================================================================
def get_latest_versions(plugins):
    plugins = [(name, LooseVersion(version)) for (name, version) in plugins]
    for name, grouped_plugins in itertools.groupby(plugins, key=lambda x: x[0]):
        name, loose_version = list(grouped_plugins)[-1]
        yield name, str(loose_version)
        
        
#===================================================================================================
# obtain_plugins_table
#===================================================================================================
def obtain_plugins_table(plugins, client):    
    rows = []
    RowData = namedtuple('RowData', 'text link')
    headers = ['Name', 'Version', 'Author', 'Summary']
    
    # pluginname and latest version, pypi link, maintainer/author, repository link,
    # one-line description, test status py27/py33
    for package_name, version in plugins:
        release_data = client.release_data(package_name, version)
        row = (
            RowData(package_name, release_data['package_url']),
            RowData(version, release_data['release_url']),
            RowData(release_data['author'], release_data['author_email']),
            RowData(release_data['summary'], None),
        )
        assert len(row) == len(headers)
        rows.append(row)
        
    return headers, rows    


#===================================================================================================
# generate_plugins_index_from_table
#===================================================================================================
def generate_plugins_index_from_table(headers, rows, basename):
        
    def get_row_limiter(char):
        return ' '.join(char * length for length in column_lengths)
    
    def ref(s, link):
        return s + '_' if link else s
    
    table_texts = []
    for row in rows:
        row_texts = []
        for i, row_data in enumerate(row): 
            text = '`%s <%s>`_' % (row_data.text, row_data.link) if row_data.link else row_data.text
            row_texts.append(text)
        table_texts.append(row_texts)
        
    column_lengths = [len(x) for x in headers]
    for row_texts in table_texts:
        for i, row_text in enumerate(row_texts):
            column_lengths[i] = max(column_lengths[i], len(row_text) + 2)
    
    with file(basename, 'w') as f:
        print >> f, '.. _plugins_index:'
        print >> f
        print >> f, 'List of Third-Party Plugins'
        print >> f, '==========================='
        print >> f
        print >> f
        print >> f, get_row_limiter('=')
        for i, header in enumerate(headers):
            print >> f, '{:^{fill}}'.format(header, fill=column_lengths[i]),
        print >> f
        print >> f, get_row_limiter('=')
        
        for row_texts in table_texts:
            for i, row_text in enumerate(row_texts):
                print >> f, '{:^{fill}}'.format(row_text, fill=column_lengths[i]),
            print >> f
        print >> f
        print >> f, get_row_limiter('=')
        print >> f


#===================================================================================================
# generate_plugins_index
#===================================================================================================
def generate_plugins_index(client, basename):
    plugins = get_latest_versions(iter_pypi_plugins(client))
    headers, rows = obtain_plugins_table(plugins, client)
    generate_plugins_index_from_table(headers, rows, basename)
    

#===================================================================================================
# main
#===================================================================================================
def main(argv):
    client = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
    basename = os.path.join(os.path.dirname(__file__), 'plugins_index.txt')
    generate_plugins_index(client, basename)
    print 'OK'
    return 0

#===================================================================================================
# main
#===================================================================================================
if __name__ == '__main__':
    sys.exit(main(sys.argv))
