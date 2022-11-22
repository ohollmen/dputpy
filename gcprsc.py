# Manipulations to resource
import copy
import json # dumps()
rattrs = ["resource","assetType","project","fpath", "memsetcnt"]
xattrs = ["exp", "role", "memcnt", "mem"]
attrs_all = copy.deepcopy(rattrs)
attrs_all.extend(xattrs)
cfg = {}

# Run cleanup and initialization tasks on a GCP resource.
# indexes (projidx, fldidx) are essential to pass here between
# calls to maintain preoper indexing (even if the default to empty dict).
def rsc_init(r, **kwargs):
  projidx = kwargs.get("projidx", {})
  fldidx  = kwargs.get("fldidx", {})
  #if : kwargs.get("projidx")
  del r["organization"]
  # Sets of members (per role)
  mss = memsets(r) # r.get("policy", {}).get("bindings")
  mscnt = len(mss)
  #print(str(mscnt) + " Member sets")
  r["memsetcnt"] = mscnt
  #r["atbn"] = os.path.basename(r.get("assetType")) # No need to strip / Keep for completeness
  r["fpath"]    = folderpath(r, trans=fldidx)
  if r.get("folders"): del r["folders"]
  # Condense and strip redundant parts (that do not bring info value)
  r["resource"] = r["resource"].replace("//", "")
  r["resource"] = r["resource"].replace(".googleapis.com", "")
  r["assetType"] = r["assetType"].replace(".googleapis.com", "")
  r["project"]  = r.get("project", "").replace("projects/", "")  
  pid = r.get("project")
  if pid and projidx.get(pid): r["project"] = projidx.get(pid).get("projectId")
  return

# Access .policy.bindings (in a safe way)
def memsets(r):
  return r.get("policy", {}).get("bindings")
# 
def folderpath(r, **kwargs):
  farr = []
  tr = kwargs.get("trans")
  for f in r.get("folders", []):
    f2 = f.replace("folders/", "")
    # Try translate
    if tr and tr.get(f2):
      trent = tr.get(f2)
      #f3 = tr.get(f2, {}).get("displayName", "")
      f3 = trent.get("displayName", "")
      if not f3: print("Trans failed: "+ f2 + " by " + json.dumps(trent))
      else:
        # print("Translated: "+f2+" => "+ f3);
        f2 = f3
    else:
      #print("Not translated: "+ f2)
      pass
    farr.append(f2)
  # Set to "fpath"
  return "/".join(farr)

def add_user_roles(r, user_role):
  mss = memsets(r)
  # Array of roles
  for rm in mss:
     # Array can have ents w. .condition.expression
     rx = rm["role"] # Role
     for m in rm["members"]:
      # 
      if not user_role.get(m): user_role[m] = {}
      user_role[m][rx] = 1
  return

# Flatten resource, Create (multiple) rows into the CSV
def createrows(r, arr):
  mss = memsets(r)
  # .policy.bindings (list)
  for rm in mss:
    e = basecopy(r) # Base for row
    # description/title
    if rm.get("condition"): e["exp"] = rm.get("condition", {}).get("title")
    else: e["exp"] = ""
    e["role"] = rm["role"]
    mems = rm["members"]
    e["memcnt"] = len(mems)
    for m in mems:
      #if m: continue
      # https://stackoverflow.com/questions/5105517/deep-copy-of-a-dict-in-python
      e2 = copy.deepcopy(e)
      e2["mem"] = m
      arr.append(e2);
  return

def basecopy(r):
  e = {}
  for a in rattrs:
    e[a] = r.get(a)
  return e
