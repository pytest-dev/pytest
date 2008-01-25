
import py

class TestCollectonly:
    def setup_class(cls):
        tmp = py.test.ensuretemp('itemgentest')
        tmp.ensure("__init__.py")
        tmp.ensure("test_one.py").write(py.code.Source("""
        def test_one():
            pass

        class TestX:
            def test_method_one(self):
                pass

        class TestY(TestX):
            pass
        """))
        tmp.ensure("test_two.py").write(py.code.Source("""
        import py
        py.test.skip('xxx')
        """))
        tmp.ensure("test_three.py").write("xxxdsadsadsadsa")
        cls.tmp = tmp

    def test_collectonly(self):
        config = py.test.config._reparse([self.tmp, '--collectonly'])
        session = config.initsession()
        # test it all in once
        cap = py.io.StdCaptureFD()
        session.main()
        out, err = cap.reset()
        # XXX exact output matching
        lines = """<Directory 'itemgentest'>
  <Module 'test_one.py'>
    <Function 'test_one'>
    <Class 'TestX'>
      <Instance '()'>
        <Function 'test_method_one'>
    <Class 'TestY'>
      <Instance '()'>
        <Function 'test_method_one'>
  <Module 'test_three.py'>
    - FAILED TO LOAD MODULE -
  <Module 'test_two.py'>
    - skipped -
"""
        for line in lines:
            assert line in out
