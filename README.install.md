# Getting and Installing dputpy

dputpy is a Python(3) module and needs to be installed in proper location
to be easily discoverable by python3 interpreter.

dputpy also contains a few command line utilities, which need to be
discoverable in shell $PATH to be easily executed.

## Discovering Python(3) library paths (sys.path)

In Linux OS and on a Mac with brew package management system the Python modules may be installed under a path like `/usr/local/lib/python3.11/site-packages`.

Find out your exact python library paths by:
```
# All paths
python3 -c 'import sys; print(sys.path)'
# Last path
python3 -c 'import sys; print(sys.path[-1])'
```
Usually the last path component will be similar to above and is the
one you should focus on (This path will be used in the next step).
Look for an item that starts with pattern: `/usr/local/lib/python*`
(may end with site-packages (Mac Brew) or dist-packages (Linux/Ubuntu)).

## Installing dputpy

In either option you will need a working git installation (to clone the dputpy repo).

**Option 1**: Change directory to the (/user/local/lib/*) path (discovered in earlier steps) and clone the repo (e.g. for Mac/Brew):

```
cd /usr/local/lib/python3.11/site-packages && git clone https://github.com/ohollmen/dputpy
```

This will clone the dputpy library to a location where it will be noticed.

**Option 2**: Alternatively you can clone library elsewhere (e.g. under your home
directory) and symlink it from there:

```
cd /usr/local/lib/python3.11/site-packages && ln -s ~/dputpy/ dputpy
```

Replace the `~/dputpy/` in above with path where you cloned the dputpy.

## Adding Essential Binaries To $PATH

Add binaries of dputpy `bin/` directory to path where they will be searched / found from.

Either use one of the existing paths in $PATH and symlink them from
(e.g.) /usr/local/lib/python3.11/site-packages/dputpy/bin/*.py by:
```
pushd /usr/local/bin && ln -s /usr/local/lib/python3.11/site-packages/dputpy/bin/*.py ./
```

Alternatively add (e.g.) `/usr/local/lib/python3.11/site-packages/dputpy/bin/`
to your path (permanently) in e.g. your .bashrc file (by adding to it ...):
```
export PATH=$PATH:/usr/local/lib/python3.11/site-packages/dputpy/bin/
```
