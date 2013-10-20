import os
import xmlrpclib

import pytest


#===================================================================================================
# test_plugins_index
#===================================================================================================
def test_plugins_index(tmpdir, monkeypatch):
    '''
    Blackbox testing for plugins_index script. Calls main() generating a file and compares produced
    output to expected.
    
    .. note:: if the test fails, a file named `test_plugins_index.obtained` will be generated in
    the same directory as this test file. Ensure the contents are correct and overwrite
    the global `expected_output` with the new contents. 
    '''
    import plugins_index
    
    # dummy interface to xmlrpclib.ServerProxy
    class DummyProxy(object):
        
        expected_url = 'http://dummy.pypi'
        def __init__(self, url):
            assert url == self.expected_url
        
        def search(self, query):
            assert query == {'name' : 'pytest-'}
            return [
                {'name': 'pytest-plugin1', 'version' : '0.8'},
                {'name': 'pytest-plugin1', 'version' : '1.0'},
                {'name': 'pytest-plugin2', 'version' : '1.2'},
            ]
            
        def release_data(self, package_name, version):
            results = {
                ('pytest-plugin1', '1.0') : {
                    'package_url' : 'http://plugin1',
                    'release_url' : 'http://plugin1/1.0',
                    'author' : 'someone',
                    'author_email' : 'someone@py.com',
                    'summary' : 'some plugin',
                    'downloads': {'last_day': 1, 'last_month': 4, 'last_week': 2},
                },
                
                ('pytest-plugin2', '1.2') : {
                    'package_url' : 'http://plugin2',
                    'release_url' : 'http://plugin2/1.2',
                    'author' : 'other',
                    'author_email' : 'other@py.com',
                    'summary' : 'some other plugin',
                    'downloads': {'last_day': 10, 'last_month': 40, 'last_week': 20},
                },
            }
            
            return results[(package_name, version)]
            
    
    monkeypatch.setattr(xmlrpclib, 'ServerProxy', DummyProxy, 'foo')
    monkeypatch.setattr(plugins_index, '_get_today_as_str', lambda: '2013-10-20')
    
    output_file = str(tmpdir.join('output.txt'))
    assert plugins_index.main(['', '-f', output_file, '-u', DummyProxy.expected_url]) == 0
    
    with file(output_file, 'rU') as f:
        obtained_output = f.read()

        if obtained_output != expected_output:
            obtained_file = os.path.splitext(__file__)[0] + '.obtained'
            with file(obtained_file, 'w') as f:
                f.write(obtained_output)

        assert obtained_output == expected_output


expected_output = '''\
.. _plugins_index:

List of Third-Party Plugins
===========================

============================================ ============================= ========= ===================
                    Name                                Author             Downloads       Summary      
============================================ ============================= ========= ===================
 `pytest-plugin1-1.0 <http://plugin1/1.0>`_   `someone <someone@py.com>`_      4         some plugin    
 `pytest-plugin2-1.2 <http://plugin2/1.2>`_     `other <other@py.com>`_       40      some other plugin 

============================================ ============================= ========= ===================

*(Downloads are given from last month only)*

*(Updated on 2013-10-20)*
'''


#===================================================================================================
# main
#===================================================================================================
if __name__ == '__main__':
    pytest.main()