

def test_parametrize(testdir):
    testdir.makepyfile("""
        import pytest

        @pytest.fixture
        def myfixture():
            return 'example'


        @pytest.mark.parametrize(
            'limit',
            (
                0,
                '0',
                'foo',
            )
        )
        def test_limit(limit, myfixture):
            return
    """)
    reprec = testdir.runpytest()
    assert 'KeyError' in reprec.stdout
