#!/usr/bin/env python3
# Tentative (WIP) setup.py for dputpy.
# https://docs.python.org/3/distutils/setupscript.html
# Optionally have setup.cfg (ini file)
# https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/
from distutils.core import setup

setup(name='dputpy', version='1.0',author='Olli Hollmen',
  description='DevOps Data Processing Utility Toolkit (Python Edition)',
  url='',
  # Only for  single-file Python modules that aren’t part of a package
  #py_modules=['dputil', 'indexer'],
  # Full packages found in setup.py root
  # Must have foo/__init__.py
  #packages=['foo', 'foo.command'],
  packages=['dputpy'],
  #package_dir={'mypkg': 'src/mypkg'},
  package_dir={'dputpy': '.'},
  #scripts=['bin/drproc.py', 'scripts/b'],
  scripts=['bin/drproc.py', 'bin/podlist.py', 'bin/tmplgen.py'],
  #data_files=[('', [])
  #install_requires=['']
)
