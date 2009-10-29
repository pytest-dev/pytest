# conftest.py 
import py


def pytest_addoption(parser):
    grp = parser.getgroup("testserver options") 
    grp.addoption("--url", action="store", default=None,
        help="url for testserver") 

def pytest_funcarg__url(request): 
    url = request.config.getvalue("url") 
    if url is None: 
        py.test.skip("need --url") 
    return url 

