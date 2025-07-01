#!/usr/bin/env python3
# Parse and Transform TF files (E.g. to generate documentation, code, reports, statistics via analytics).
# pip3 install python-hcl2
import hcl2
import json
import argparse
import dputpy.clapp as clapp
import dputpy.dputil as dputil
import sys # sys.argv
# Load and Parse TF HCL2 file.
# Data (by hcl2 library) is laid out so that e.g. multiple individual "variable" declarations
# are located (each) in an array ("variable": [{}, {}, ..., {}]). There are also 
def tf_load(fn, **kwargs):
  fh = open(fn, 'r')
  dict = hcl2.load(fh)
  # Example of accessing particular branch within structure
  if kwargs.get("debug"): jstr = json.dumps(dict, indent=2); print(jstr) # e.g. dict.get("variable")
  sect = kwargs.get("sect")
  if sect:
    sa = dict.get(sect)
    if not sa: print("No Section '"+sect+"' available in TF (Has: "+str(list(dict.keys()))+")."); return None
    return sa
  return dict

# Turn TF vars to more simple format and avoid the "arbitrary key" problem.
# TODO: See if this transformation pattern is applicable to more than vars.
def tfvars_simplify(arr):
  for it in arr:
    ks = list( it.keys() )
    if len(ks) > 1: print("Multiple keys found - unexpected !"); return None;
    o = it.get(ks[0])
    if not isinstance(o, dict): print("The single-key is not valued to dict"); return None;
    # Early delete of key, as 1) we do have a ref "o" above. 2) There may be a clash in keys (e.g. "name")
    del it[ks[0]]
    #it.pop(ks[0], None) # Should also work (2nd param None must be present to avoid KeyError)
    it["varname"] = ks[0] # Set as name (Only "name" ?)
    for k in o.keys(): it[k] = o[k]
    
  return arr
# CL Handler for loading and transforming TF to simplified AoO (LoD) fmt.
# Output to stdout.
def tftrans(opts):
  fn = opts.get("fn")
  sect = opts.get("sect") or "variable"
  #sect = "output"
  tfopts = {"sect": sect}
  #tfopts["debug"] = 1
  arr = tf_load(fn, **tfopts)
  #print(json.dumps(arr, indent=2))
  if not arr: usage("Could not get section '"+sect+"' from parsed TF. Try passing --sect a_valid_key.");
  arr = tfvars_simplify(arr)
  print(json.dumps(arr, indent=2));
  return

# Pull terraform state
def st_pull(**kwargs):
  bcmd = "terraform"
  if kwargs.get("basecmd"): bcmd = kwargs.get("basecmd")
  cmd = f"{bcmd} state pull"
  # Run and parse ...
  st = None
  ret = dputil.run(cmd, fmt="json", debug=1) # onerror
  if ret.get("rc"): raise ValueError(f"Error {ret.get('rc')} in running {cmd}")
  st = ret.get("out")
  if not st: raise ValueError("Could not parse TF State JSON")
  return st
def state_rm(**kwargs): # Pass type(name, str), elem(dict) ?
  bcmd = "terraform"
  if kwargs.get("basecmd"): bcmd = kwargs.get("basecmd")
  cmd = f"{bcmd} state rm"
  # ret = dputil.run(cmd,  debug=1) # fmt="json", onerror
  # if ret.get("rc"): 
  return
# Access resource branch in terraform state (st)
# Allow
# TODO: raise ValueError() on failed access
def st_get(st, key, etype):
  if not st: return None
  if not key: raise ValueError("No key passed !")
  # Pre-populate some
  etypes = st.get("resources")
  if not etypes: return None
  if not isinstance(etypes, dict): return None
  # Type list
  if etype == 'rtypes':
    return etypes
  ############################## 
  # Instance ?
  etypes.get(key);
  return None
# Get instance list for particular TF type.
# On caller side the next likely step is to get instance (e.g.):
# ```
#  instlist = tfiac.st_instance_list(st, "my_tf_type")
#  key = ""
#  inst_l = list(filter(lambda(x): ..., instlist))
#  if len(ilist_l) != 1: raise ValueError(f"'{key}' - Not a singular instance !")
#  # E.g. Get name, run state rm ...
#  #
# ```
def st_instance_list(st, etype):
  ilist = st_get(st, key, 'inst')
  #if not ilist: raise ValueError(f"Could not get instance list for type {etype}")
  return ilist
#######################################################

def usage(msg):
  if msg: print(msg)
  exit(1)
ops = {
  
}
if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='TF Parser/Transformer') # prog= ???
  parser.add_argument('--sect',  default="variable", help='Section name of TF file.') # nargs=1/+
  
  #cla = clapp.new(ops)
  #clapp.clparse(cla)
  #pargs = parser.parse_args() # nnn.py: error: unrecognized arguments: ...
  pargs, rawargs = parser.parse_known_args() # https://stackoverflow.com/questions/17118999/python-argparse-unrecognized-arguments
  opts = vars(pargs) # sys.argv / sys.argv[1:]
  #print(opts);print(rawargs);exit(0);
  #opts = {} # {"fn": sys.argv[1]}
  if len(rawargs): opts["fn"] = rawargs[0] # sys.argv[1]
  else: print("No args !"); exit(1)
  tftrans(opts)
  exit(0)
