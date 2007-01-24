# XXX this file is messy since it tries to deal with several docutils versions
import py

from py.__.rest.convert import convert_dot, latexformula2png

import sys
import docutils
from docutils import nodes
from docutils.parsers.rst import directives, states, roles
from docutils.parsers.rst.directives import images

if hasattr(images, "image"):
    directives_are_functions = True
else:
    directives_are_functions = False

try:
    from docutils.utils import unescape # docutils version > 0.3.5
except ImportError:
    from docutils.parsers.rst.states import unescape # docutils 0.3.5

if not directives_are_functions:
    ImageClass = images.Image

else:
    class ImageClass(object):
        option_spec = images.image.options
        def run(self):
            return images.image(u'image',
                                self.arguments,
                                self.options,
                                self.content,
                                self.lineno,
                                self.content_offset,
                                self.block_text,
                                self.state,
                                self.state_machine)


backend_to_image_format = {"html": "png", "latex": "pdf"}

class GraphvizDirective(ImageClass):
    def convert(self, fn, path):
        path = py.path.local(path).dirpath()
        dot = path.join(fn)
        result = convert_dot(dot, backend_to_image_format[_backend])
        return result.relto(path)

    def run(self):
        newname = self.convert(self.arguments[0],
                               self.state.document.settings._source)
        text = self.block_text.replace("graphviz", "image", 1)
        self.block_text = text.replace(self.arguments[0], newname, 1)
        self.name = u'image'
        self.arguments = [newname]
        return ImageClass.run(self)
    
    def old_interface(self):
        def f(name, arguments, options, content, lineno,
              content_offset, block_text, state, state_machine):
            for arg in "name arguments options content lineno " \
                       "content_offset block_text state state_machine".split():
                setattr(self, arg, locals()[arg])
            return self.run()
        f.arguments = (1, 0, 1)
        f.options = self.option_spec
        return f


_backend = None
def set_backend_and_register_directives(backend):
    #XXX this is only used to work around the inflexibility of docutils:
    # a directive does not know the target format
    global _backend
    _backend = backend
    if not directives_are_functions:
        directives.register_directive("graphviz", GraphvizDirective)
    else:
        directives.register_directive("graphviz",
                                      GraphvizDirective().old_interface())
    roles.register_canonical_role("latexformula", latexformula_role)

def latexformula_role(name, rawtext, text, lineno, inliner,
                      options={}, content=[]):
    if _backend == 'latex':
        options['format'] = 'latex'
        return roles.raw_role(name, rawtext, text, lineno, inliner,
                              options, content)
    else:
        # XXX: make the place of the image directory configurable
        sourcedir = py.path.local(inliner.document.settings._source).dirpath()
        imagedir = sourcedir.join("img")
        if not imagedir.check():
            imagedir.mkdir()
        # create halfway senseful imagename:
        # use hash of formula + alphanumeric characters of it
        # could
        imagename = "%s_%s.png" % (
            hash(text), "".join([c for c in text if c.isalnum()]))
        image = imagedir.join(imagename)
        latexformula2png(unescape(text, True), image)
        imagenode = nodes.image(image.relto(sourcedir), uri=image.relto(sourcedir))
        return [imagenode], []
latexformula_role.content = True
latexformula_role.options = {}

def register_linkrole(role_name, callback):
    def source_role(name, rawtext, text, lineno, inliner, options={},
                    content=[]):
        text, target = callback(name, text)
        reference_node = nodes.reference(rawtext, text, name=text, refuri=target)
        return [reference_node], []
    source_role.content = True
    source_role.options = {}
    roles.register_canonical_role(role_name, source_role)
