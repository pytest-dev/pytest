"""
thin wrapper around Python's optparse.py  
adding some extra checks and ways to systematically
have Environment variables provide default values
for options.  basic usage:

   >>> parser = Parser()
   >>> parser.addoption("--hello", action="store_true", dest="hello")
   >>> option, args = parser.parse(['--hello'])
   >>> option.hello 
   True
   >>> args
   []
    
"""
import py
import optparse 

class Parser:
    """ Parser for command line arguments. """ 

    def __init__(self, usage=None, processopt=None):
        self._anonymous = OptionGroup("custom options", parser=self)
        self._groups = []
        self._processopt = processopt
        self._usage = usage 
        self.hints = []

    def processoption(self, option):
        if self._processopt:
            if option.dest:
                self._processopt(option)

    def addnote(self, note):
        self._notes.append(note)

    def getgroup(self, name, description="", after=None):
        for group in self._groups:
            if group.name == name:
                return group
        group = OptionGroup(name, description, parser=self)
        i = 0
        for i, grp in enumerate(self._groups):
            if grp.name == after:
                break
        self._groups.insert(i+1, group)
        return group 

    addgroup = getgroup 
    def addgroup(self, name, description=""):
        py.log._apiwarn("1.1", "use getgroup() which gets-or-creates")
        return self.getgroup(name, description)

    def addoption(self, *opts, **attrs):
        """ add an optparse-style option. """
        self._anonymous.addoption(*opts, **attrs)

    def parse(self, args):
        optparser = MyOptionParser(self)
        groups = self._groups + [self._anonymous]
        for group in groups:
            if group.options:
                desc = group.description or group.name 
                optgroup = optparse.OptionGroup(optparser, desc)
                optgroup.add_options(group.options)
                optparser.add_option_group(optgroup)
        return optparser.parse_args([str(x) for x in args])

    def parse_setoption(self, args, option):
        parsedoption, args = self.parse(args)
        for name, value in parsedoption.__dict__.items():
            setattr(option, name, value)
        return args


class OptionGroup:
    def __init__(self, name, description="", parser=None):
        self.name = name
        self.description = description
        self.options = []
        self.parser = parser 

    def addoption(self, *optnames, **attrs):
        """ add an option to this group. """
        option = optparse.Option(*optnames, **attrs)
        self._addoption_instance(option, shortupper=False)

    def _addoption(self, *optnames, **attrs):
        option = optparse.Option(*optnames, **attrs)
        self._addoption_instance(option, shortupper=True)

    def _addoption_instance(self, option, shortupper=False):
        if not shortupper:
            for opt in option._short_opts:
                if opt[0] == '-' and opt[1].islower(): 
                    raise ValueError("lowercase shortoptions reserved")
        if self.parser:
            self.parser.processoption(option)
        self.options.append(option)


class MyOptionParser(optparse.OptionParser):
    def __init__(self, parser):
        self._parser = parser 
        optparse.OptionParser.__init__(self, usage=parser._usage)
    def format_epilog(self, formatter):
        hints = self._parser.hints 
        if hints:
            s = "\n".join(["hint: " + x for x in hints]) + "\n"
            s = "\n" + s + "\n"
            return s
        return ""
