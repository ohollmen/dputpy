# Typical modification and transformations patterns to entries.
# Example:
# import dputpy.xform as xform
# TODO: Module name: iter, foreach. Allow filter=1 option

# Transform Objects in AoO or OoO (inner nodes)
# Params in kwargs:
# - userdata: additional userdata parameter to call the callback with
def xform(data, cb, **kwargs):
  #if not isinstance(cb, dict):
  udata = kwargs.get("userdata")
  if isinstance(data, dict):
    for k in data.keys():
      o = data[k]
      if udata: cb(o, udata)
      else: cb(o)
  elif isinstance(data, list):
    for o in data:
      if udata: cb(o, udata)
      else: cb(o)
  else: print("Not iterating/transforming (Not an dict/list)");return
  return data

#def filter()

def props_del(d, props):
  for key in props: it.pop(key, None)

def index_by(arr, prop):
  #if not isinstance(arr, list): print("Can't index a non-list"); return
  return {it[prop]: it  for it in arr}
