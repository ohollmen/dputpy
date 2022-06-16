# indexer.index(arr, keyattr, ...)
# Create indexed dict-of-dicts out of array-of-dicts
# KW Args supported:
# - idx - Allow passing index to add to (instead of creating a new fresh index, this
#  way indexing can be done incrementally)
# - udata - Pass userdata to callback (default: none)
# - precb - Pre-prep callback which is called with precb(item, udata), where userdata (udata) defaults to null
# Return index dictionary (either new or one passed by "idx" KW arg).
def index(arr, keyattr, **kwargs):
  idx = {}
  udata = None
  if kwargs.get('idx'): idx = kwargs.get('idx')
  if kwargs.get('udata'): udata = kwargs.get('udata')
  precb = kwargs.get('precb')
  if kwargs.get('prepcb'): precb = kwargs.get('prepcb')
  if not precb: precb = None # Check function
  i = 0
  for it in arr:
    if precb:
      precb(it, udata)
    # Must keep **after** precb, because keyattr might be generated
    if not it.get(keyattr): print("No value for key attribute "+ keyattr+" (Item idx="+i+")");
    idx[it[keyattr]] = it
    i += 1
  return idx

# Development time tester to see if particular dict key has non-unique items
# TODO: Implement this by means of idx=idx, udata=idx, precb=already_in_index
# Return number of cases where overlapping keys were found.
def nonunique(arr, keyattr):
  idx = {}
  nonuni = 0
  for it in arr:
    if idx.get(it[keyattr]): nonuni += 1
    idx[it[keyattr]] = 1 # Just mark (do not index item)
  return nonuni

# Ways to access github repo .tar.gz. pip(3) has some level of support for this
# but the dir structure has to "comply" (setyp.py on top, ...).
# Note: wget / curl output slightly different
# python3 -m pip install https://github.com/ohollmen/dputpy/archive/09f1772b669f48ed05695bd13b9ced36d84be415.tar.gz
#   has sub-path: dputpy-09f1772b669f48ed05695bd13b9ced36d84be415
# pip3 install https://github.com/ohollmen/dputpy/tarball/master
# https://github.com/ohollmen/dputpy/tarball/master has sub-path ohollmen-dputpy-09f1772
# ## Refs
# https://stackoverflow.com/questions/8247605/configuring-so-that-pip-install-can-work-from-github
# Hint: git clone .../foo.git; cd foo; pip install -e .  (-e / --editable)
