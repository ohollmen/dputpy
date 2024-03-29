# Services Config (and access)

import dputpy.ansdi as adi
import dputpy.dputil as dputil
svs = None
# Need top-level / inv ???
hmap = None

def new(_svs, _inv):
  global svs
  if not _svs: print("svs: No services passed !!");exit(1)
  if not _inv: print("svs: No inventory passed !!");exit(1)
  svs = _svs
  # TODO: hmap = adi.hmap_get()
  hmap = inv.get("_meta", {}).get("hostvars", {})
  if not hmap: print("No hmap accessible"); exit(1)
  return 1

def reverse(svs, mcfg):
  for s in svs:
    if s.get("hapair"): s.get("hapair").reverse()
    if s.get("halbip"): s.get("halbip").reverse()
    if s.get("hasubnets"): s.get("hasubnets").reverse()
    if s.get("snapschds"): s.get("snapschds").reverse()
    if s.get("kubenvs"): s.get("kubenvs").reverse()
  # Top-level
  if mcfg and mcfg.get("envnames"):
    mcfg.get("envnames").reverse()
  return
# Init / Prepare services
# TODO: Could init and reverse separately. Note: reverse might imply partial re-init (!!), e.g. envnames
# (... or anything in A,B arrays)
def init(svs, mcfg, rev): # **kwargs
  iso = dputil.isotime(date=1)
  #print("Initing "+str(len(svs))+" svs ...");
  for s in svs:
    #img = re.search(r'snapshot', s.get("hatype", ""))
    #hnode = hnode_get()
    dn = s.get("domainname");
    if not dn: s["domainname"] = mcfg["domainname"]
    # GCP/DNS Conv done has '-'
    s["domainzone"] = s["domainname"].replace(".", "-");
    haimg = s.get("haimgbn", "") # bn ?
    # Use curr. date (== make a good guess)
    if haimg:
      s["haimg"] = s["haimgbn"] + "-" + iso
      #print("Generated dated image name for serv "+ s["title"] + " ("+s["haimg"]+")");
    # Need to reverse array-val'd props
    # TODO: kwargs.get("rev")
    arrprops = ["hapair", "halbip", "hasubnets", "snapschds", "kubenvs", "clusters", "regions"]
    if rev: # TODO: Check type == list
      if s.get("hapair"): s.get("hapair").reverse()
      if s.get("halbip"): s.get("halbip").reverse()
      if s.get("hasubnets"): s.get("hasubnets").reverse()
      if s.get("snapschds"): s.get("snapschds").reverse()
      # K8S src,tgt arrays
      if s.get("kubenvs"): s.get("kubenvs").reverse()
      if s.get("clusters"): s.get("clusters").reverse()
      if s.get("regions"): s.get("regions").reverse() # used ?
  ####### mcfg #####
  if mcfg and mcfg.get("envnames") and rev:
    mcfg.get("envnames").reverse()
  # Update separate members on mcfg
  # Check, validate ?
  mcfg["envname_a"] = mcfg.get("envnames")[0]
  mcfg["envname_b"] = mcfg.get("envnames")[1]
  if not mcfg.get("isodate"): mcfg["isodate"] = dputil.isotime(date=1)
  
  # NOT in loop
  return

def vm_get_byname(vmname):
  #
  return

# Get VM by "hapair" index 0 (A, src) / 1 (B/dest)
def vm_get_idx(s, idx): # vmname
  if not isinstance(s, dict): print("Service not passed as dict"); exit(1)
  pair = s.get("hapair")
  if not isinstance(pair, list): print("Service VM pair is not a list"); exit(1)
  if (len(pair) < 2) or (len(pair) > 2): print("Service VM pair len != 2"); exit(1)
  h = adi.hnode_get( pair[idx] ) # OLD: s.get("hapair")[idx]
  if not isinstance(h, dict): print("Service VM object is not dict"); exit(1)
  return h

# Lookup subnet to dr in-to
def subnet_dr(s):
  snets = s.get("hasubnets");
  if not snets: return None
  if not isinstance(snets, list): return None
  return snets[1]
