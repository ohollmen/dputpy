# Create indexed dict-of-dicts out of array-of-dicts

# TODO: idx - Allow passing index to add to
# udata - Pass userdata to callback (default: none)
def index(arr, keyattr, **kwargs):
  idx = {}
  udata = None
  if kwargs.get('idx'): idx = kwargs.get('idx')
  if kwargs.get('udata'): udata = kwargs.get('udata')
  precb = kwargs.get('precb')
  if not precb: precb = None
  i = 0
  for it in arr:
    if precb:
      precb(it, udata)
    if not it.get(keyattr): print("No value for key attribute "+ keyattr+" (Item idx="+i+")");
    idx[it[keyattr]] = it
    i += 1
  return idx

# Development time tester to see if particular dict key has non-unique items
# TODO: Implement this by means of idx=idx, udata=idx, precb=already_in_index
def nonunique(arr, keyattr):
  idx = {}
  nonuni = 0
  for it in arr:
    if idx.get(it[keyattr]): nonuni += 1
    idx[it[keyattr]] = 1 # Just mark (do not index item)
  return nonuni
