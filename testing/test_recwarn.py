import warnings
import re
import py
import pytest


def test_recwarn_functional(testdir):
    testdir.makepyfile("""
        import warnings

        def test_method(recwarn):
            warnings.warn("hello")
            warn = recwarn.pop()
            assert isinstance(warn.message, UserWarning)
    """)
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(['* 1 passed *'])


class TestWarningsRecorderChecker(object):

    def test_recording(self, testdir):
        testdir.makepyfile('''
            import pytest
            import warnings

            def test(recwarn):
                assert len(recwarn) == 0
                assert len(recwarn.list) == 0
                warnings.warn_explicit("hello", UserWarning, "xyz", 13)
                assert len(recwarn.list) == 1
                warnings.warn(DeprecationWarning("hello"))
                assert len(recwarn.list) == 2
                warn = recwarn.pop()
                assert str(warn.message) == "hello"
                l = recwarn.list
                recwarn.clear()
                assert len(recwarn.list) == 0
                assert l is recwarn.list
                with pytest.raises(AssertionError):
                    recwarn.pop()
        ''')
        result = testdir.runpytest()
        result.stdout.fnmatch_lines(['* 1 passed *'])

    def test_type_checking(self, testdir):
        testdir.makepyfile('''
            import pytest

            @pytest.mark.parametrize('v', [5, ('hi', RuntimeWarning), [DeprecationWarning, RuntimeWarning]])
            def test(v):
                with pytest.raises(TypeError):
                    pytest.warns(v)
        ''')
        result = testdir.runpytest()
        result.stdout.fnmatch_lines(['* 3 passed *'])

    def test_invalid_enter_exit(self, testdir):
        testdir.makepyfile('''
            import pytest

            def test(recwarn):
                with pytest.raises(RuntimeError):
                    with recwarn:
                        pass
        ''')
        result = testdir.runpytest()
        result.stdout.fnmatch_lines(['* 1 passed *'])


class TestDeprecatedCall(object):
    """test pytest.deprecated_call()"""

    def dep(self, i, j=None):
        if i == 0:
            py.std.warnings.warn("is deprecated", DeprecationWarning,
                                 stacklevel=1)
        return 42

    def dep_explicit(self, i):
        if i == 0:
            py.std.warnings.warn_explicit("dep_explicit", category=DeprecationWarning,
                                          filename="hello", lineno=3)

    def test_deprecated_call_raises(self):
        with pytest.raises(AssertionError) as excinfo:
            pytest.deprecated_call(self.dep, 3, 5)
        assert str(excinfo).find("did not produce") != -1

    def test_deprecated_call(self):
        pytest.deprecated_call(self.dep, 0, 5)

    def test_deprecated_call_ret(self):
        ret = pytest.deprecated_call(self.dep, 0)
        assert ret == 42

    def test_deprecated_explicit_call_raises(self):
        with pytest.raises(AssertionError):
            pytest.deprecated_call(self.dep_explicit, 3)

    def test_deprecated_explicit_call(self):
        pytest.deprecated_call(self.dep_explicit, 0)
        pytest.deprecated_call(self.dep_explicit, 0)

    def test_deprecated_call_as_context_manager_no_warning(self):
        with pytest.raises(pytest.fail.Exception, matches='^DID NOT WARN'):
            with pytest.deprecated_call():
                self.dep(1)

    def test_deprecated_call_as_context_manager(self):
        with pytest.deprecated_call():
            self.dep(0)

    def test_deprecated_call_pending(self):
        def f():
            py.std.warnings.warn(PendingDeprecationWarning("hi"))
        pytest.deprecated_call(f)

    def test_deprecated_call_specificity(self):
        other_warnings = [Warning, UserWarning, SyntaxWarning, RuntimeWarning,
                          FutureWarning, ImportWarning, UnicodeWarning]
        for warning in other_warnings:
            def f():
                py.std.warnings.warn(warning("hi"))
            with pytest.raises(AssertionError):
                pytest.deprecated_call(f)

    def test_deprecated_function_already_called(self, testdir):
        """deprecated_call should be able to catch a call to a deprecated
        function even if that function has already been called in the same
        module. See #1190.
        """
        testdir.makepyfile("""
            import warnings
            import pytest

            def deprecated_function():
                warnings.warn("deprecated", DeprecationWarning)

            def test_one():
                deprecated_function()

            def test_two():
                pytest.deprecated_call(deprecated_function)
        """)
        result = testdir.runpytest()
        result.stdout.fnmatch_lines('*=== 2 passed in *===')


class TestWarns(object):
    def test_strings(self):
        # different messages, b/c Python suppresses multiple identical warnings
        source1 = "warnings.warn('w1', RuntimeWarning)"
        source2 = "warnings.warn('w2', RuntimeWarning)"
        source3 = "warnings.warn('w3', RuntimeWarning)"
        pytest.warns(RuntimeWarning, source1)
        pytest.raises(pytest.fail.Exception,
                      lambda: pytest.warns(UserWarning, source2))
        pytest.warns(RuntimeWarning, source3)

    def test_function(self):
        pytest.warns(SyntaxWarning,
                     lambda msg: warnings.warn(msg, SyntaxWarning), "syntax")

    def test_warning_tuple(self):
        pytest.warns((RuntimeWarning, SyntaxWarning),
                     lambda: warnings.warn('w1', RuntimeWarning))
        pytest.warns((RuntimeWarning, SyntaxWarning),
                     lambda: warnings.warn('w2', SyntaxWarning))
        pytest.raises(pytest.fail.Exception,
                      lambda: pytest.warns(
                          (RuntimeWarning, SyntaxWarning),
                          lambda: warnings.warn('w3', UserWarning)))

    def test_as_contextmanager(self):
        with pytest.warns(RuntimeWarning):
            warnings.warn("runtime", RuntimeWarning)

        with pytest.warns(UserWarning):
            warnings.warn("user", UserWarning)

        with pytest.raises(pytest.fail.Exception) as excinfo:
            with pytest.warns(RuntimeWarning):
                warnings.warn("user", UserWarning)
        excinfo.match(r"DID NOT WARN. No warnings of type \(.+RuntimeWarning.+,\) was emitted. "
                      r"The list of emitted warnings is: \[UserWarning\('user',\)\].")

        with pytest.raises(pytest.fail.Exception) as excinfo:
            with pytest.warns(UserWarning):
                warnings.warn("runtime", RuntimeWarning)
        excinfo.match(r"DID NOT WARN. No warnings of type \(.+UserWarning.+,\) was emitted. "
                      r"The list of emitted warnings is: \[RuntimeWarning\('runtime',\)\].")

        with pytest.raises(pytest.fail.Exception) as excinfo:
            with pytest.warns(UserWarning):
                pass
        excinfo.match(r"DID NOT WARN. No warnings of type \(.+UserWarning.+,\) was emitted. "
                      r"The list of emitted warnings is: \[\].")

        warning_classes = (UserWarning, FutureWarning)
        with pytest.raises(pytest.fail.Exception) as excinfo:
            with pytest.warns(warning_classes) as warninfo:
                warnings.warn("runtime", RuntimeWarning)
                warnings.warn("import", ImportWarning)

        message_template = ("DID NOT WARN. No warnings of type {0} was emitted. "
                            "The list of emitted warnings is: {1}.")
        excinfo.match(re.escape(message_template.format(warning_classes,
                                                        [each.message for each in warninfo])))


    def test_record(self):
        with pytest.warns(UserWarning) as record:
            warnings.warn("user", UserWarning)

        assert len(record) == 1
        assert str(record[0].message) == "user"

    def test_record_only(self):
        with pytest.warns(None) as record:
            warnings.warn("user", UserWarning)
            warnings.warn("runtime", RuntimeWarning)

        assert len(record) == 2
        assert str(record[0].message) == "user"
        assert str(record[1].message) == "runtime"

    def test_record_by_subclass(self):
        with pytest.warns(Warning) as record:
            warnings.warn("user", UserWarning)
            warnings.warn("runtime", RuntimeWarning)

        assert len(record) == 2
        assert str(record[0].message) == "user"
        assert str(record[1].message) == "runtime"

        class MyUserWarning(UserWarning): pass

        class MyRuntimeWarning(RuntimeWarning): pass

        with pytest.warns((UserWarning, RuntimeWarning)) as record:
            warnings.warn("user", MyUserWarning)
            warnings.warn("runtime", MyRuntimeWarning)

        assert len(record) == 2
        assert str(record[0].message) == "user"
        assert str(record[1].message) == "runtime"

    def test_double_test(self, testdir):
        """If a test is run again, the warning should still be raised"""
        testdir.makepyfile('''
            import pytest
            import warnings

            @pytest.mark.parametrize('run', [1, 2])
            def test(run):
                with pytest.warns(RuntimeWarning):
                    warnings.warn("runtime", RuntimeWarning)
        ''')
        result = testdir.runpytest()
        result.stdout.fnmatch_lines(['*2 passed in*'])
