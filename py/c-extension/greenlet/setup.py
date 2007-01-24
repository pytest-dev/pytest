from distutils.core import setup
from distutils.extension import Extension

setup (	name             = "greenlet",
      	version          = "0.1",
      	ext_modules=[Extension(name = 'greenlet',
                               sources = ['greenlet.c'])]
        )
