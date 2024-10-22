
import sys
import copy

def both_are(i1, i2, t):
  if not isinstance(i1, t): return False
  if not isinstance(i2, t): return False
  return True

def dict_merge_defs(dictn, defs, **kwargs):
  if not isinstance(dictn, dict): return None
  if not isinstance(defs, dict): return None
  defkeys = kwargs.get("defkeys") or defs.keys()
  print("Keys driving merge (default): "+str(defkeys));
  for dk in defkeys:
    if not dk in dictn:
      # Note: value can be any type, must stringify
      print("Adding/merging missing k-v: "+dk+"="+str(defs[dk])+"", file=sys.stderr) # 
      dictn[dk] = defs[dk]
  return dictn

def items_merge(a1, a2):
  if not isinstance(a1, list): print("Not an array - array 1"); return 1
  if not isinstance(a2, list): print("Not an array - array 2"); return 1
  #if not isinstance(defs, dict): print("No defs in dict"); return 2
  # Conservative approach - go by size of shorter array
  size = min(len(a1), len(a2))
  i = 0
  while i < size:
    print("Got "+str(a1[i]) );
    if a1[i] == None: a1[i] = copy.deepcopy(a2[i]) # Duplicate/Clone
    elif both_are(a1[i], a2[i], dict):
      dict_merge_defs(a1[i], a2[i])
    elif both_are(a1[i], a2[i], str) and not a1[i]:
      a1[i] = a2[i]
    #yield start
    i += 1

# TODO
# - Test deepcopy on string: ????
