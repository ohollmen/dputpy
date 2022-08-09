# Set operations (aka Boolean Operations) for lists and dicts.
# When dict:s are passed, assumes that dictionary keys have a true
# value for them (i.e. not 0, or None or "").
# TODO: convert to exists()-logic (allow falsy value ?)
def diff(a,b, **kwargs):
  if type(a) is list: a = todict(a)
  if type(b) is list: b = todict(b)
  d = {} # Delta / Diff
  for k in a.keys():
    if not b.get(k): d[k] = True
  if kwargs.get("asarray"): d = tolist(d)
  return d

# TODO: Allow either list or dict
def union(a,b):
  u = {}
  # Count ?
  for k in a: u[k] = True
  for k in b: u[k] = True
  return list(u.keys())

def intersect(a,b, **kwargs):
  isect = {}
  if type(a) is list: a = todict(a)
  if type(b) is list: b = todict(b)
  for k in a.keys():
    if b.get(k): isect[k] = True
  for k in b.keys():
    if a.get(k): isect[k] = True
  if kwargs.get("asarray"): isect = tolist(isect)
  return isect

def todict(arr):
  d = {}
  for it in arr:
    #if d[it]: d[it] += 1
    #else d[it] = 1
    d[it] = True # Count ?
  return d

def tolist(d):
  if not type(d) is list: return d # Throw ? No need
  return list( d.keys() )
