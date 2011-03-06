from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

myext = Extension('handlers', ['handlers.pyx'])
setup(cmdclass={'build_ext' : build_ext}, ext_modules=[myext])
