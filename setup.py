#!/usr/bin/env python3
# Tentative (WIP) setup.py for dputpy.
# https://docs.python.org/3/distutils/setupscript.html
# Optionally have setup.cfg (ini file)
from distutils.core import setup

setup(name='dputpy', version='1.0',author='Olli Hollmen',
  description='DevOps Data Processing Utility Toolkit (Python Edition)',
  url='',
  py_modules=['dputil', 'indexer'],
  # Full packages found in setup.py root
  # Must have foo/__init__.py
  #packages=['foo', 'foo.command'],
  #package_dir={'mypkg': 'src/mypkg'},
  #scripts=['scripts/a', 'scripts/b'],
  #data_files=[('', [])
)
