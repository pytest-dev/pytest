import uuid
import py
from pytest_resultlog import ResultLog

class ResultdbPlugin:
    """XXX in progress: resultdb plugin for database logging of test results. 

    Saves test results to a datastore.

    Also mixes in some early ideas about an archive abstraction for test 
    results.
    """ 
    def pytest_addoption(self, parser):
        group = parser.addgroup("resultdb", "resultdb plugin options")
        group.addoption('--resultdb', action="store", dest="resultdb", 
                metavar="path",
                help="path to the file to store test results.")
        group.addoption('--resultdb_format', action="store", 
                dest="resultdbformat", default='json',
                help="data format (json, sqlite)")
    
    def pytest_configure(self, config):
        if config.getvalue('resultdb'):
            if config.option.resultdb:
                # local import so missing module won't crash py.test
                try:
                    import sqlite3
                except ImportError:
                    raise config.Error('Could not import sqlite3 module')
                try:
                    import simplejson
                except ImportError:
                    raise config.Error('Could not import simplejson module')
                if config.option.resultdbformat.lower() == 'json':
                    self.resultdb = ResultDB(JSONResultArchive, 
                            config.option.resultdb) 
                elif config.option.resultdbformat.lower() == 'sqlite':
                    self.resultdb = ResultDB(SQLiteResultArchive, 
                            config.option.resultdb) 
                else:
                    raise config.Error('Unknown --resultdb_format: %s' % 
                            config.option.resultdbformat) 

                config.bus.register(self.resultdb)

    def pytest_unconfigure(self, config):
        if hasattr(self, 'resultdb'):
            del self.resultdb 
            #config.bus.unregister(self.resultdb)


class JSONResultArchive(object):
    def __init__(self, archive_path):
        self.archive_path = archive_path
        import simplejson
        self.simplejson = simplejson
        
    def init_db(self):
        if os.path.exists(self.archive_path):
            data_file = open(self.archive_path)
            archive = self.simplejson.load(data_file)
            self.archive = archive
        else:
            self.archive = []
            self._flush()

    def append_data(self, data):
        runid = uuid.uuid4()
        for item in data:
            item = item.copy()
            item['runid'] = str(runid)
            self.archive.append(item)
            self._flush()

    def get_all_data(self):
        return self.archive

    def _flush(self):
        data_file = open(self.archive_path, 'w')
        self.simplejson.dump(self.archive, data_file)
        data_file.close()


class SQLiteResultArchive(object):
    def __init__(self, archive_path):
        self.archive_path = archive_path
        import sqlite3
        self.sqlite3 = sqlite3
        
    def init_db(self):
        if not os.path.exists(self.archive_path):
            conn = self.sqlite3.connect(self.archive_path)
            cursor = conn.cursor()
            try:
                cursor.execute(SQL_CREATE_TABLES)
                conn.commit()
            finally:
                cursor.close()
                conn.close()

    def append_data(self, data):
        flat_data = []
        runid = uuid.uuid4()
        for item in data:
            item = item.copy()
            item['runid'] = str(runid)
            flat_data.append(self.flatten(item))
        conn = self.sqlite3.connect(self.archive_path)
        cursor = conn.cursor()
        cursor.executemany(SQL_INSERT_DATA, flat_data)
        conn.commit()
        cursor.close()
        conn.close()

    def get_all_data(self):
        conn = self.sqlite3.connect(self.archive_path)
        conn.row_factory = self.sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(SQL_SELECT_DATA)
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        data = [self.unflatten(item) for item in data]
        return data

    def flatten(self, item):
        return (item.get('runid', None),
                item.get('name', None),
                item.get('passed', False),
                item.get('skipped', False),
                item.get('failed', False),
                item.get('shortrepr', None),
                item.get('longrepr', None),
                item.get('fspath', None),
                item.get('itemname', None),
                )

    def unflatten(self, item):
        names = ("runid name passed skipped failed shortrepr "
                "longrepr fspath itemname").split()
        d = {}
        for i, name in enumerate(names):
            d[name] = item[i]
        return d


class ResultDB(ResultLog):
    def __init__(self, cls, db_path):
        self.archive = cls(db_path)
        self.archive.init_db()

    def write_log_entry(self, testpath, shortrepr, longrepr):
        data = {}
        event_excludes = ['colitem', 'longrepr']
        for item in vars(event).keys():
            if item not in event_excludes:
                data[item] = getattr(event, item)
        # use the locally calculated longrepr & shortrepr        
        data['longrepr'] = longrepr
        data['shortrepr'] = shortrepr

        data['testpath'] = unicode(testpath)
        self.archive.append_data([data])


SQL_CREATE_TABLES = """
create table pytest_results (
    runid varchar(36),
    name varchar,
    passed int,
    skipped int,
    failed int,
    shortrepr varchar,
    longrepr varchar,
    fspath varchar,
    itemname varchar
    );
"""
SQL_INSERT_DATA = """
insert into pytest_results (
    runid,
    name,
    passed,
    skipped,
    failed,
    shortrepr,
    longrepr,
    fspath,
    itemname)
values (?, ?, ?, ?, ?, ?, ?, ?, ?);          
"""
SQL_SELECT_DATA = """
select 
    runid,
    name,
    passed,
    skipped,
    failed,
    shortrepr,
    longrepr,
    fspath,
    itemname
from pytest_results;
"""


# ===============================================================================
#
# plugin tests 
#
# ===============================================================================

import os, StringIO

class BaseResultArchiveTests(object):
    cls = None

    def setup_class(cls):
        # XXX refactor setup into a funcarg? 
        cls.tempdb = "test_tempdb"

    def test_init_db(self, testdir):
        tempdb_path = unicode(testdir.tmpdir.join(self.tempdb))
        archive = self.cls(tempdb_path)
        archive.init_db()
        assert os.path.exists(tempdb_path)

    def test_db_insert(self, testdir):
        tempdb_path = unicode(testdir.tmpdir.join(self.tempdb))
        archive = self.cls(tempdb_path)
        archive.init_db()
        assert len(archive.get_all_data()) == 0

        data = [{'name': 'tmppackage/test_whatever.py:test_hello',
                    'fspath': '/Users/brian/work/tmppackage/test_whatever.py',
                    'name': 'test_hello',
                    'longrepr': '',
                    'passed': True,
                    'shortrepr': '.'
                }]
        archive.append_data(data)
        result = archive.get_all_data()
        print result
        assert len(result) == 1
        for key, value in data[0].items():
            assert value == result[0][key]
        assert 'runid' in result[0]
        
        # make sure the data is persisted
        tempdb_path = unicode(testdir.tmpdir.join(self.tempdb))
        archive = self.cls(tempdb_path)
        archive.init_db()
        assert len(archive.get_all_data()) == 1


class TestJSONResultArchive(BaseResultArchiveTests):
    cls = JSONResultArchive

    def setup_method(self, method):
        py.test.importorskip("simplejson")

    
class TestSQLiteResultArchive(BaseResultArchiveTests):
    cls = SQLiteResultArchive

    def test_init_db_sql(self, testdir):
        tempdb_path = unicode(testdir.tmpdir.join(self.tempdb))
        archive = self.cls(tempdb_path)
        archive.init_db()
        assert os.path.exists(tempdb_path)
        
        # is table in the database? 
        import sqlite3
        conn = sqlite3.connect(tempdb_path)
        cursor = conn.cursor()
        cursor.execute("""SELECT name FROM sqlite_master
                        ORDER BY name;""")
        tables = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(tables) == 1
    
def verify_archive_item_shape(item):
    names = ("runid name passed skipped failed shortrepr "
                "longrepr fspath itemname").split()
    for name in names:
        assert name in item

class TestWithFunctionIntegration:
    def getarchive(self, testdir, arg):
        py.test.importorskip("simplejson")
        resultdb = testdir.tmpdir.join("resultdb")
        args = ["--resultdb=%s" % resultdb, "--resultdb_format=sqlite"] + [arg]
        testdir.runpytest(*args)
        assert resultdb.check(file=1)
        archive = SQLiteResultArchive(unicode(resultdb))
        archive.init_db()
        return archive
        
    def test_collection_report(self, plugintester):
        py.test.skip("Needs a rewrite for db version.")
        testdir = plugintester.testdir()
        ok = testdir.makepyfile(test_collection_ok="")
        skip = testdir.makepyfile(test_collection_skip="import py ; py.test.skip('hello')")
        fail = testdir.makepyfile(test_collection_fail="XXX")

        lines = self.getresultdb(testdir, ok) 
        assert not lines

        lines = self.getresultdb(testdir, skip)
        assert len(lines) == 2
        assert lines[0].startswith("S ")
        assert lines[0].endswith("test_collection_skip.py")
        assert lines[1].startswith(" ")
        assert lines[1].endswith("test_collection_skip.py:1: Skipped: 'hello'")

        lines = self.getresultdb(testdir, fail)
        assert lines
        assert lines[0].startswith("F ")
        assert lines[0].endswith("test_collection_fail.py"), lines[0]
        for x in lines[1:]:
            assert x.startswith(" ")
        assert "XXX" in "".join(lines[1:])

    def test_log_test_outcomes(self, plugintester):
        testdir = plugintester.testdir()
        mod = testdir.makepyfile(test_mod="""
            import py 
            def test_pass(): pass
            def test_skip(): py.test.skip("hello")
            def test_fail(): raise ValueError("val")
        """)

        archive = self.getarchive(testdir, mod)
        data = archive.get_all_data()
        for item in data:
            verify_archive_item_shape(item)
        assert len(data) == 3
        assert len([item for item in data if item['passed'] == True]) == 1
        assert len([item for item in data if item['skipped'] == True]) == 1
        assert len([item for item in data if item['failed'] == True]) == 1

    def test_internal_exception(self):
        py.test.skip("Needs a rewrite for db version.")
        # they are produced for example by a teardown failing
        # at the end of the run
        try:
            raise ValueError
        except ValueError:
            excinfo = py.code.ExceptionInfo()
        reslog = ResultDB(StringIO.StringIO())        
        reslog.pyevent__internalerror(excinfo.getrepr)
        entry = reslog.logfile.getvalue()
        entry_lines = entry.splitlines()

        assert entry_lines[0].startswith('! ')
        assert os.path.basename(__file__)[:-1] in entry_lines[0] #.py/.pyc
        assert entry_lines[-1][0] == ' '
        assert 'ValueError' in entry  

def test_generic(plugintester):
    plugintester.apicheck(ResultdbPlugin)
    testdir = plugintester.testdir()
    testdir.makepyfile("""
        import py
        def test_pass():
            pass
        def test_fail():
            assert 0
        def test_skip():
            py.test.skip("")
    """)
    testdir.runpytest("--resultdb=result.sqlite")
    #testdir.tmpdir.join("result.sqlite")
    
