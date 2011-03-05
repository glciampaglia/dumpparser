from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

myext = Extension('_dumpparser', ['_dumpparser.pyx'])


setup(
        cmdclass = {'build_ext':build_ext},
        ext_modules = [ myext ]
)
