# DevOps Data Processing Utility Toolkit (for Python)

Python dputpy (dput = Data Processing Utility toolkit) is a library for
modern devops automation involving

- Reading, Writing, Transforming Files (e.g. JSON, YAML, INI, CSV, ...)
- Setting up and validating and testing arbitrary host environments (On-Prem, Cloud, Baremetal, VM, mixture of previous).

# Installing dputpy

dputpy as a module/package is in "standard" Python pakage format, but
is not (yet?) available in PyPI (Python Package Index). As such it is
handiest installed (directly from GitHub) by:
```
# Simple installation scenario
pip3 install https://github.com/ohollmen/dputpy/archive/master.zip
# If python complains about not installing in pyenv based environment:
pip3 install --break-system-packages https://github.com/ohollmen/dputpy/archive/master.zip
```
This ZIP package based installation makes PIPm download the GitHub repo (in
standard Python package format) as ZIP file (a feature supported by
GitHub) and install it from that Zipped Python package file.
The location of installation may vary by OS (Linux, MacOS, Windows).

With good luck the PYTHONPATH environment variable or runtime sys.path
(both reflecting Python library path) will point to path locations
where dputpy was installed. If you need one of the executables in
dputpy `bin` directory, make sure to have that in OS environment
`$PATH` variable (Note: to adjust PYTHONPATH or PATH for dputpy you
first have to know where pip installed it, skim the output of `pip3
install ...` for clues on that).


# Using dputpy in a Python Project

Example of using various dputpy modules in your project
```
# Load 
import dputpy.dputil as dputil
# Start using ...
jdata = dputil.jsonload("./my.conf.json")
```

# Copyright and License

Olli Hollmen (2020-2022), License: MIT

# History

dputpy aims to have similar nature (mission, functionality) as its counterpart [DPUT](https://github.com/ohollmen/DPUT) (written in Perl).
Both toolkits were born out of the (same) need to minimize low-level tasks (code writing) during real life automation creation.
These repeating tasks patterns are thus collected to libraries with flexible and generic (easy-to-use) API interfaces.

# Installation and dependencies

Most dependencies of dputpy are mainly fairly straight forward and written
in "pure python (i.e. without bindings to C or C++ runtime). One
exception to this is pyyaml Cloader (helpful for speeding up parsing with
large-size YAML files).

# The "Python hell" mess that Brew and RedHat Linux create

MacOS Brew and RHEL tend to believe that the more you have Python
versions you have, the merrier the life will be. Most users found the
opposite to be true. Example of reviewing python files (modules)
under /usr/local:

```
# *.py under /usr/local (Brew, Gcloud)
mrsmith$ find /usr/local/ -name "*.py" | wc -l
   51177
# Unique directories where *.py was installed
find /usr/local/ -name "*.py" | xargs -n 1 dirname | sort -u | wc -l
```
Form output it can often be seen that we have modules installed under (e.g.)
python 3.6, 3.8, 3.10, 3.11 site directories, each of which is "visible"
only to particular version of python and installed modules are thus "lost"
when moving to a new python.

Forcing pyyaml to install under current version of python:
```
# Initial problem state: Launch script depending on pyyaml
myscript.py
...
ImportError: cannot import name 'CLoader' from 'yaml' (unknown location)
/usr/local/bin/python3 /usr/local/bin/pip3 install pyyaml
# Launch again - should work now
myscript.py
...
```
