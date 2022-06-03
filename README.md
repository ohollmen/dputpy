# DevOps Data Processing Utility Toolkit (for Python)

Python dputpy (dput = Data Processing Utility toolkit) is a library for
modern devops automation involving

- Reading, Writing, Transforming Files (e.g. JSON, YAML, INI, CSV, ...)
- Setting up and validating and testing arbitrary host environments (On-Prem, Cloud, Baremetal, VM, mixture of previous).

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
