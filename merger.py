# Various data (structure) merging operations.
import sys
import copy

# ## both_are(data1, data2, typerequirement)
# Helper function to test if both datastructures / collections (or primitives) are of same type (passed as 3rd param).
# 
def both_are(i1, i2, t):
  if not isinstance(i1, t): return False
  if not isinstance(i2, t): return False
  return True

# Show self-data and defaults (in that order) for debugging purposes.
def both_show(d1, d2):
  print("Data-Dest: ", d1)
  print("Defaults : ", d2)

# dict_merge_defs(dest, src, kwargs)
# Merge a dict (defs) to base-dict when a key is missing
# Keyword args supported (as kwargs):
# - defkeys - use particular subset of keys to drive the merging
#   (Example: `dict_merge_defs({a: v1}, {b: v2: c: v3}, defkeys=["b"]);`
# - debug - turn on debug messages
def dict_merge_defs(dictn, defs, **kwargs):
  if not isinstance(dictn, dict): return None
  if not isinstance(defs, dict): return None
  defkeys = kwargs.get("defkeys") or defs.keys()
  #attrs = kwargs.get("attrs") # passed subset of attrs / keys
  #if attrs and isinstance(attrs, list): defkeys = attrs
  debug = kwargs.get("debug")
  if debug: print("- Keys driving merge (default): "+str(defkeys));
  for dk in defkeys:
    if not dk in dictn:
      # Note: value can be any type, must stringify
      if debug: print("- Adding/merging missing k-v: "+dk+"="+str(defs[dk])+"", file=sys.stderr)
      dictn[dk] = defs[dk]
  return dictn

# Merge 2 arrays a1 (base to merge to) and a2 (merge from) element-to-element:
# - Support merges of array items/elements that are dict or string
# - source (a2) and dest (a1) must be of same type for merge to happen (i.e dict & dict or sting & string)
# - When *both* are dict:
#   - If dest is None, make a complete copy.deepcopy of source dict
#   - (else ...) do basic defaults merge (missing in dest are copied/defaulted)
# - When *both* are str:  merge value from source if dest value is falsy
def arrays_merge(a1, a2, **kwargs):
  if not isinstance(a1, list): print("Not an array - array 1"); return 1
  if not isinstance(a2, list): print("Not an array - array 2"); return 1
  #if not isinstance(defs, dict): print("No defs in dict"); return 2
  debug = kwargs.get("debug")
  # Conservative approach - go by size of shorter array
  size = min(len(a1), len(a2))
  i = 0
  while i < size:
    if debug: print("- MM-Got "+str(a1[i]) );
    if a1[i] == None: a1[i] = copy.deepcopy(a2[i]) # Dest None(null) - Duplicate/Clone src as-is
    elif both_are(a1[i], a2[i], dict): # Basic merge defaults
      dict_merge_defs(a1[i], a2[i])
    elif both_are(a1[i], a2[i], str) and not a1[i]: # String merge
      a1[i] = a2[i]
    #yield start
    i += 1

# TODO
# - Test deepcopy on string: ????
