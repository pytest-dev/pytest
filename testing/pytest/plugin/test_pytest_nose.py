import py
py.test.importorskip("nose")

def test_nose_setup(testdir):
    p = testdir.makepyfile("""
        l = []

        def test_hello():
            assert l == [1]
        def test_world():
            assert l == [1,2]
        test_hello.setup = lambda: l.append(1)
        test_hello.teardown = lambda: l.append(2)
    """)
    result = testdir.runpytest(p, '-p', 'nose')
    result.stdout.fnmatch_lines([
        "*2 passed*"
    ])

def test_nose_test_generator_fixtures(testdir):
    p = testdir.makepyfile("""
        # taken from nose-0.11.1 unit_tests/test_generator_fixtures.py
        from nose.tools import eq_
        called = []

        def outer_setup():
            called.append('outer_setup')

        def outer_teardown():
            called.append('outer_teardown')

        def inner_setup():
            called.append('inner_setup')

        def inner_teardown():
            called.append('inner_teardown')

        def test_gen():
            called[:] = []
            for i in range(0, 5):
                yield check, i
                
        def check(i):
            expect = ['outer_setup']
            for x in range(0, i):
                expect.append('inner_setup')
                expect.append('inner_teardown')
            expect.append('inner_setup')
            eq_(called, expect)

            
        test_gen.setup = outer_setup
        test_gen.teardown = outer_teardown
        check.setup = inner_setup
        check.teardown = inner_teardown

        class TestClass(object):
            def setup(self):
                print "setup called in", self
                self.called = ['setup']

            def teardown(self):
                print "teardown called in", self
                eq_(self.called, ['setup'])
                self.called.append('teardown')

            def test(self):
                print "test called in", self
                for i in range(0, 5):
                    yield self.check, i

            def check(self, i):
                print "check called in", self
                expect = ['setup']
                #for x in range(0, i):
                #    expect.append('setup')
                #    expect.append('teardown')
                #expect.append('setup')
                eq_(self.called, expect)

    """)
    result = testdir.runpytest(p, '-p', 'nose')
    result.stdout.fnmatch_lines([
        "*10 passed*"
    ])



def test_module_level_setup(testdir):
    testdir.makepyfile("""
        from nose.tools import with_setup
        items = {}
        def setup():
            items[1]=1

        def teardown():
            del items[1]

        def setup2():
            items[2] = 2

        def teardown2():
            del items[2]

        def test_setup_module_setup():
            assert items[1] == 1

        @with_setup(setup2, teardown2)
        def test_local_setup():
            assert items[2] == 2
            assert 1 not in items

    """)
    result = testdir.runpytest('-p', 'nose')
    result.stdout.fnmatch_lines([
        "*2 passed*",
    ])

def test_nose_style_setup_teardown(testdir):
    testdir.makepyfile("""
        l = []
        def setup_module():
            l.append(1)

        def teardown_module():
            del l[0]

        def test_hello():
            assert l == [1]

        def test_world():
            assert l == [1]
        """)
    result = testdir.runpytest('-p', 'nose')
    result.stdout.fnmatch_lines([
        "*2 passed*",
    ])

