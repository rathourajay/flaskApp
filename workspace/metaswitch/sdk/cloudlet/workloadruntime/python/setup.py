from distutils.core import setup, Extension

module1 = Extension('ensiwc',
                    extra_compile_args = ['-Wno-write-strings'],
                    sources = ['ensiwcpython.cpp', 'ensiwcworkload.cpp', 'enslog.cpp', 'ensiwcmem.cpp'])

setup (name = 'ensiwc',
       version = '1.0',
       description = 'ENS interworkload communications',
       ext_modules = [module1])
