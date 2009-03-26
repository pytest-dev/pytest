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
from py.compat import optparse

class Parser:
    """ Parser for command line arguments. """ 

    def __init__(self, usage=None, processopt=None):
        self._anonymous = OptionGroup("custom options", parser=self)
        self._groups = [self._anonymous]
        self._processopt = processopt
        self._usage = usage 

    def processoption(self, option):
        if self._processopt:
            if option.dest:
                self._processopt(option)

    def addgroup(self, name, description=""):
        for group in self._groups:
            if group.name == name:
                raise ValueError("group %r already exists" % name)
        group = OptionGroup(name, description, parser=self)
        self._groups.append(group)
        return group 

    def getgroup(self, name):
        for group in self._groups:
            if group.name == name:
                return group
        raise ValueError("group %r not found" %(name,))

    def addoption(self, *opts, **attrs):
        """ add an optparse-style option. """
        self._anonymous.addoption(*opts, **attrs)

    def parse(self, args):
        optparser = optparse.OptionParser(usage=self._usage)
        # make sure anaonymous group is at the end 
        groups = self._groups[1:] + [self._groups[0]]
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
        option = py.compat.optparse.Option(*optnames, **attrs)
        self._addoption_instance(option, shortupper=False)

    def _addoption(self, *optnames, **attrs):
        option = py.compat.optparse.Option(*optnames, **attrs)
        self._addoption_instance(option, shortupper=True)

    def _addoption_instance(self, option, shortupper=False):
        if not shortupper:
            for opt in option._short_opts:
                if opt[0] == '-' and opt[1].islower(): 
                    raise ValueError("lowercase shortoptions reserved")
        if self.parser:
            self.parser.processoption(option)
        self.options.append(option)

        
