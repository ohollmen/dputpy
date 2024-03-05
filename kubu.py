# Kubernetes Utilities
# Works largely based on config with:
# - cluster (AoS) - The list of cluster names
# - OLD: prefix (str) - prefix for the cluster podlist 
# ## Notes on image id
# - In docker image ls output the image hash is titled "IMAGE ID" (e.g. f1cb7c7d58b7)
# - docker image inspect f1cb7c7d58b7 creates a detailed JSON output, where
#   - "Id": "sha256:f1cb7c7d58b73eac859c395882eec49d50651244e342cd6c68a5c7809785f427", # Matching "IMAGE ID" (at start)
#   - "RepoDigests": [ "centos@sha256:62d9e1c2daa91166139b51577fe4f4f6b4cc41a3a2c7fc36bd895e2a17a3e4e6"], # Room for Multiple ?
#   - "Layers": [ "sha256:89169d87dbe2b72ba42bfbb3579c957322baca28e03a1e558076542a1c1b2b4a"]
# - In an build/extended image
#   - the first layer is same as the only layer of base image
#   - "RepoDigests": [], # is empty on a local (basename) image - always ?
#   - RepoDigests may contain server/pathsteps/imagename@sha256:hash"
# ## image id vs. repo digest
# - image id - from local JSON manifest
# - repo digest - gets generated after pulling or pushing image
# # Other
# - https://cloud.google.com/sdk/gcloud/reference/container/images/list
# gcloud container images list --repository=gcr.io/myproject --format json
import dputpy.dputil as dputil
#import json
import os # os.path.basename(path)
import re
import sys

allowcfg = {
  # Tweak based on presence and correctness of headings, delimiter/separator
  "sep": ',', "skipfirst": 1,
  #"fldnames": ["scandate","image","repo_digest", "_img_id"],
  #"fldnames": ["scandate","imgfull","sha256sum", "img_id"],
  "fldnames": ["scandate","maintainer", "img", "tag", "sha256sum"], # , "img_id"
  "debug": 0
}
nslist = None
# Simple pod filtering
def podfilter(p):
  if not nslist: print("Error: nslist is not set !!!", file=sys.stderr); exit(1)
  m = p.get("metadata", None)
  if not m: return 0
  ns = m.get("namespace", "")
  #print("Got ns = "+ns);
  # Exclude (return 0)
  if ns and nslist: # and (ns in nslist)
    for npr in nslist:
      if npr.search(ns):
        #print("Exclude: "+ns);
        return 0
  return 1
    
# Load and Merge/aggergate Multi Cluster Pod List
# Create a linear list of pods from one or more cluster pod listings gotten with (-A = all namespaces):
#     kubectl get pods -A -o json
# Note: Info has to be  ...
# Pod listings are expected to be stored in files (created earlier e.g. with the help of podlist.py "gencmds" subcommand).
def mc_pods(cfg, **kwargs):
  cs = cfg.get("clusters")
  mcpods_all = []
  prefix = cfg.get("prefix") or "podlist."
  path = cfg.get("podinfopath")
  # if re.search(r'\{\{', cfg.get("clusterfntmpl") ): 
  debug = cfg.get("debug") or kwargs.get("debug")
  for cn in cs:
    fn = path + "podlist."+cn+".json"
    if debug: print("Try loading "+ fn, file=sys.stderr);
    j = dputil.jsonload(fn)
    pods = j.get("items")
    mcpods_all += pods
    # TODO: Add/Inject cluster name cn
    for p in pods: p["cluster"] = cn
  # Optional: Filter
  nsf = cfg.get("nsfilter", {})
  # kwargs.get("filter", 0) and
  if nsf and nsf.get("exc"): # Add: .. and is list
    if debug: print("Perform Filtering of type exc. w. "+ str(len( nsf.get("exc") )) + " patterns", file=sys.stderr);
    global nslist
    nslist = []
    nslist_l = nsf.get("exc")
    for pat in nslist_l:
      nslist.append( re.compile(pat) )
    #print("Starting filter by ", nslist);
    mcpods_all = list( filter(podfilter, mcpods_all) )
    
  if kwargs.get("debug"): print("Got "+str(len(mcpods_all))+" pods");
  return mcpods_all


# Lowest level image status collection from Pod status (containerStatuses / initContainerStatuses)
# Create object with members
# - img - Image basename (w/o) tag
# - imgfull - Image full path with tag
# - tag tag part of image URL (part after ':')
# - sha256sum
# ## Additional notes
# In the containerStatuses node "state" member, state.waiting maybe set with:
# "state": {
#      "waiting": {
#          "message": "Back-off pulling image \"gcr.io/spgovusm1-saas-gke1/spgovusm1saasgke1/cert-manager/cert-manager-ctl:v1.9.1-20220914\"",
#          "reason": "ImagePullBackOff"
#      }
#  }
# And additionally "imageID": "", (empty, luckily still splittable/parseable string). Skip these cases !
def contstat_get_img(cs):
  e = {}
  # No imageID (for e.g. state.waiting = {message: "Back-off pulling image...", reason: "ImagePullBackOff"})
  if not cs.get("imageID"): print("Pod w/o imageID/SHA256 ", file=sys.stderr); return None
  ii = cs.get("image").split(":")
  ii2 = cs.get("imageID").split("@")
  if ii[0] != ii2[0]:
    #print("Images not same: '"+ii[0]+"' vs. '"+ii2[0]+"'")
    if ii2[0].find("sha256", 0) < 0: ii2 = [ None, ii2[0] ]
    #return
  #else: print("Images ARE same !")
  if len(ii2) == 1:
    #print("Have: "+json.dumps(ii2))
    ii2 = [ None, ii2[0] ]
    #ii2.append("")
  e["img"] = ii[0]
  e["imgfull"] = cs.get("image")
  e["tag"] = ii[1]
  e["sha256sum"] = ii2[1].replace("sha256:", "")
  # Must have basename for image: os.path.basename(path) or RE or split()
  e["imgbn"] = os.path.basename(e["imgfull"])
  # Validate state.waiting
  #if not e["sha256sum"]: print("Encountered emty sha for ", e); exit(1)
  #m = e["imgfull"]
  return e

def podstat_get_imgs(p): #, pod
  st = p.get("status")
  if not st: print("No status available", file=sys.stderr); return None
  rcs = st.get("containerStatuses") # real
  ics = st.get("initContainerStatuses")
  # isinstance()
  if not rcs :
    m = p.get("metadata", {})
    n = m.get("name", "")
    ns = m.get("namespace", "") # Also "ns" ()
    print("One of essential status (rcs, ...) sections missing ("+ns+"/"+n+")!", file=sys.stderr); return
  iiset = [] # Image Info
  for ci in rcs:
    i = contstat_get_img(ci)
    if not i: continue
    iiset.append(i)
  if not ics: return iiset # No init conts ...
  for ci in ics:
    i = contstat_get_img(ci)
    if not i: continue
    iiset.append(i)
    if i: i["type"] = "init"
  return iiset


# Differentiate native pod p and summary pod
def pod_imgstats(p):
  s  = p.get("spec")
  m  = p.get("metadata")
  st = p.get("status")
  
  if not s or not m or not st: print("One of essential sections missing !", file=sys.stderr); return None
  #print("spec: "+ str( isinstance(s, dict) ) );
  #print("meta: "+ str( isinstance(m, dict) ) );
  #print("namespace: "+m.get("namespace"))
  #print("containers: "+  str( len( s.get("containers") ) ) )
  pod = { "ns": m.get("namespace"), "name": m.get("name"), "imgs": [], "cluster": p.get("cluster") }
  
  imgs = podstat_get_imgs(p)
  if imgs: pod["imgs"] = imgs
  # print(json.dumps(pod, indent=2))
  return pod

# Collect pods from multiple clusters and extract the image info from them
# (for later stats or analysis).
def imglist(cfg, **kwargs):
  mcpods = mc_pods(cfg, **kwargs)
  #if kwargs.get(""): print(json.dumps(mcpods, indent=1)) # Pods
  allimg = []
  
  for p in mcpods:
      #print(json.dumps(p, indent=1)); exit(1)
      pod = pod_imgstats(p)
      if kwargs.get("icollcb"):
        kwargs.get("icollcb")(pod)
      allimg.append(pod) # +=
  return allimg

#### Authorized images list cmp. ops ######
