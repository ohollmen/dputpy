# Ansible dynamic inventory
# - Top-level: Holistic inverntory with groups info and hosts
# - hmap: ._meta.hostvars

import re

inv = None
hmap = None

def new(_inv):
  global hmap
  global inv
  inv = _inv
  hmap = hmap_get()

def hmap_get():
  if not inv: print("No inventory registered !!"); exit(1)
  hmap = inv.get("_meta", {}).get("hostvars", {})
  return hmap

# Init hostmap: add stuff, delete stuff (index stuff ?)
def hmap_init(hmap):
  # 
  # Work on whole inv ? inv.get('_meta'). ...
  for hk in hmap.keys():
    hnode = hmap.get(hk)
    hnode["hname"] = hk;
    #delete hnode "metadata", disks.shieldedInstanceInitialState
    # metadata has also cluster-name and cluster_name, cluster-location
    del hnode['metadata'] # hnode.pop("metadata", None)
    hnode["region"] = zone2reg( hnode["zone"] ) # Add region implied by zone

# Convert zone to implied parent region
def zone2reg(z):
  r = re.sub(r'-[a-z]$', '', z)
  return r

def hnode_get(n):
  if not isinstance(hmap, dict): print("hmap (in module) is not dict"); exit(1)
  h = hmap.get(n, None)
  # if not h: 
  return h

# Query disk properties like 'deviceName' or 'diskSizeGb'
# Note: Ansible inventory does not have disk 'Name' (gcloud output does)
def hnode_disk_prop(h, prop):
  d = h.get("disks", [None])[0]
  if not d: print("No disk for host "+h); return None
  return d.get(prop)

# Get First Net-if (networkInterfaces[0])
def netif(h, **kwargs):
  nifarr = h.get("networkInterfaces")
  if not nifarr: return None
  if not nifarr[0]: return None
  if kwargs.get("ipaddr"): return nifarr[0].get("networkIP")
  if not isinstance(nifarr[0], dict): return None
  return nifarr[0]
