import py

class TestWINLocalPath:
    #root = local(TestLocalPath.root)
    disabled = py.std.sys.platform != 'win32'

    def setup_class(cls):
        cls.root = py.test.ensuretemp(cls.__name__) 

    def setup_method(self, method): 
        name = method.im_func.func_name
        self.tmpdir = self.root.ensure(name, dir=1) 

    def test_chmod_simple_int(self):
        print "self.root is", self.root
        mode = self.root.stat().st_mode
        # Ensure that we actually change the mode to something different.
        self.root.chmod(mode == 0 and 1 or 0)
        try:
            print self.root.stat().st_mode 
            print mode
            assert self.root.stat().st_mode != mode
        finally:
            self.root.chmod(mode)
            assert self.root.stat().st_mode == mode

    def test_path_comparison_lowercase_mixed(self):
        t1 = self.root.join("a_path")
        t2 = self.root.join("A_path")
        assert t1 == t1
        assert t1 == t2
        
    def test_relto_with_mixed_case(self):
        t1 = self.root.join("a_path", "fiLe")
        t2 = self.root.join("A_path")
        assert t1.relto(t2) == "fiLe"

    def test_allow_unix_style_paths(self):
        t1 = self.root.join('a_path')
        assert t1 == str(self.root) + '\\a_path'
        t1 = self.root.join('a_path/')
        assert t1 == str(self.root) + '\\a_path'
        t1 = self.root.join('dir/a_path')
        assert t1 == str(self.root) + '\\dir\\a_path'
        
