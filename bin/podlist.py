#!/usr/local/bin/python3
# --all-namespaces / -A
# # All pods aggregated
# 
# python3 podlist.py allpods | grep '"metadata"' | wc -l
# 
# python3 podlist.py imgstat | grep '"name"' | wc -l
# 
import json

import dputpy.dputil as dputil
import dputpy.kubu as kubu
import dputpy.indexer as indexer
import dputpy.xform as xform
import sys
import argparse
import re
import os
import jinja2
cfgfn = "podlist.conf.json"
cfg = dputil.jsonload(cfgfn)
imgidx = {} # Counts / Stats

# https://cloud.google.com/storage/docs/wildcards
def gen_data_cmds(): # args
  # cfg = args.get("cfg")
  cs = cfg.get("clusters")
  initcmd = cfg.get("initshellcmd", ""); itmpl = None
  if re.search(r'\{\{', initcmd): itmpl = jinja2.Template(initcmd)
  t2 = jinja2.Template("kubectl get pods -A -o json > {{ pipath }}podlist.{{ cluster }}.json")
  for c in cs:
    if itmpl: print(itmpl.render(**{"cluster": c}))
    else: print(initcmd)
    p = { "pipath": cfg.get("podinfopath", ""), "cluster": c }
    print( t2.render(**p) )
    print("exit"); # ONLY:if initcmd: ...
  if cfg.get("bucketname"):
    print("# gsutil cp podlist.*.json gs://"+cfg.get("bucketname")+"/");
    print("# gcloud auth login --no-launch-browser");
    print("# gsutil cp gs://"+cfg.get("bucketname")+"/podlist.*.json .");

# Image stat collection CB (called during imglist collection)
def iscoll(pod):
  #print("CALL CB for "+pod["name"])
  # See
  for i in pod.get("imgs", []):
    iname = i.get("img")+":"+i.get("tag")
    iitem = imgidx.get(iname)
    if not iitem: imgidx[iname] = 1
    else: imgidx[iname] += 1
  return

def servernorm(o):
  url = o.get("imgfull", "")
  url2 = o.get("img", "")
  if url: o["imgfull"] = re.sub(r'^[^/]+', "server.com", url)
  if url2: o["img"] = re.sub(r'^[^/]+', "server.com", url2)
  return
# Load Allowed-images list based on config (w. filename).
# The cols in file should be (in order):
# - rundate,
# - imgfull (path),
# - tag (image tag part NEW)
# - sha256sum (digest), this is really the column matching K8S Pod dump "imageID" (json/yaml prop)
# - OLD: image_id (Not used)
# Create member "imgbn" for the purpose of later correlating images soly by their basenames.
# Strip any (optional) "sha256:" prefix from 
# Return allowed images list (AoO, any indexing must be done by caller).
# 
def allowlist_load(cfg, **kwargs):
  if not cfg: print("No config for loading allowed-images list"); return None
  ######### Allow any aspect of CSV/TSV to be configured #######
  if cfg.get("sep"): kubu.allowcfg["sep"] = cfg.get("sep")
  if "skipfirst" in cfg: kubu.allowcfg["skipfirst"] = cfg.get("skipfirst")
  fns = cfg.get("fldnames")
  if fns and isinstance(fns, list) and len(fns): kubu.allowcfg["fldnames"] = cfg.get("fldnames")
  ######## Load ! ######
  #bn =    # Basename
  fn = cfg.get("allowlistfn")
  #if fn.endswith(".yaml") or fn.endswith(".yml"):
  #  cont = open(fn, "r").read()
  #  allow = yaml.safe_load(cont)
  #elif fn.endswith(".json"):
  #  cont = open(fn, "r").read()
  #  cfg = json.loads(cont)
  allow = dputil.csv_load(fn, **kubu.allowcfg)
  if not allow: print("No allowed-images list loaded !"); return None
  #if cfg.get("debug", 0): print("Loaded CSV: ", allow);
  if cfg.get("debug"): print("DEBUG:\n"+json.dumps(allow, indent=1))
  hash_key = "sha256sum" # OLD: repo_digest => sha256sum
  tagin = kwargs.get("tagin", "")
  # Populate / Normalize add'l fields into records (for fast comparison)
  for a in allow:
    if a.get(hash_key, "").find("sha256:", 0) > -1: a[hash_key] = a.get(hash_key).replace("sha256:", "")
    #if tagin: 
    if not a.get("imgfull"): a["imgfull"] = a.get("img") + ':' + a.get("tag")
    # "imgbn" should be basename + tag
    a["imgbn"] = os.path.basename(a.get("imgfull")) # ... with tag. Very useful for (performing) cross-correlation.
    # Additionally "bn" (from "imgbn")
    bn_tag = a["imgbn"].split(":");
    a["bn"] = bn_tag[0] # e.g. for maint. correlation
  return allow

# Check list of all images against the list of allowed images.
# Generate a third summary/report structure on non-compliant pods.
# Image entity Members
# - img - full path w/o tag (universal)
# - imgfull - full path w. tag (universal)
# - tag - tag part only (universal)
# - imgbn - image basename (last image name part) + tag (universal)
# - sha256sum - the trailing part of kubernetes pod "imageID" (with prefix "@sha256:" stripped)
#   - Gotten from section "containerStatuses", "initContainerStatuses" (NOT "containers", there's no "imageID" in that section)
# Check levels (passed in :
# - 1: Check by image basename + tag
# - 2: Additionally check sha256 checksum
def allow_check(allimg, allow_idx, **kwargs):
  counts = [0,0,0] # 
  unibad = {} # Unique bad index (key: img + tag) (val: 1)
  badpod = [] # Bad pods list (AoO) to collect
  imgcnt = 0
  debug = kwargs.get("debug")
  chklvl = kwargs.get("chklvl") or 1
  if (chklvl != 1) and (chklvl != 2): chklvl = 1
  if debug: printf("Chose check level: "+chklvl) # STDERR !
  for pis in allimg: # Pod image stats (created in kubu.imglist())
    imgs = pis["imgs"] # 1 or more images
    for i in imgs:
      #if not i.get("img"): print("img member not present ", i); continue
      #if not i.get("tag"): print("tag member not present ", i); continue
      iname_f =  i.get("img")+":"+i.get("tag") # full for reporting
      iname = i.get("imgbn") # bn + tag
      ai = allow_idx.get(iname) # ai = Allowed image (Try to lookup by basename)
      vok = 0 # Validation ok 0=not okay, 1=imagename (bn+tag) okay, 2=even digest is okay
      vmsg = iname_f + " "
      if not ai:
        vmsg += " BAD by img-bn."
        #verr += 1
      else: vmsg +=  " OK by img-bn."; vok += 1
      
      # Secondary check for digest / sha256sum
      if vok and ai: # OLD: (not verr)
        if ai.get("sha256sum") == i.get("sha256sum"): # OK, even hash matches
          # Both ok
          vmsg += " Also OK by hash."
          vok += 1 # Add to validation score +1
          #continue
        else:
          #verr += 1
          vmsg += " BAD by hash."
      counts[vok] += 1
      # Check validation score: 0,1,2. Dropped to 1 to NOT require perfect sha256 (only basename+tag)
      if vok < chklvl: # Report as non-approved
        unibad[iname_f] = 1 # TODO: cnt
        # TODO: Should create partial duplicate with imgbn
        # pis2 = deepcopy(); delete(pis2["imgs"]); badpod.append(pis2)
        pis2 = { "img": iname_f, "sha256sum": i.get("sha256sum") } # Copy most ["cluster", "ns", "name"]. Add allowed ai.get("sha256sum") ?
        for k in ["cluster", "ns", "name"]: pis2[k] = pis.get(k)
        badpod.append(pis2)
        # "' allow-sha256: '"+ai.get("sha256sum")+
      debug and print(vmsg + " pod-sha256: '" + i.get("sha256sum") + " ("+str(vok)+")");
      imgcnt += 1
  return {"counts": counts, "unibad": unibad, "imgcnt": imgcnt, "badpod": badpod}

# Report culprit pods in rudimentary Markdown (style) format.
def allow_report(cres):
  badimgs = cres.get("unibad").keys()
  cnt = len( badimgs )
  print("Images checked: "+str(cres.get("imgcnt"))+"")
  print("Disallowed (unique) images ("+str(cnt)+"):"); # TODO: Track these back to imglist
  for img in badimgs:
    print("- "+img)
  print("\nCounts of bad/allowed:")
  capt = ["Disallowed image name", "Image name OK, but digest check fails", "Imagename and digest OK"]
  i = 0
  for cnt in cres.get("counts", []):
    print("- "+capt[i] + ": "+ str(cnt));  
    i += 1
  badpods = cres.get("badpod")
  if not badpods: return 0
  print("Culprit pods (for cleanup or review):");
  for fixi in badpods:
    #maint = fixi.get("maint");
    print("- "+fixi.get("img", "")+" ("+fixi.get("sha256sum", "")+")");
    print("  - Cluster: "+fixi.get("cluster")+",  NS: "+fixi.get("ns")+",  Podname: "+fixi.get("name")+"");

def imgstat(): # args
  # cfg = args.get("cfg")
  allimg = kubu.imglist(cfg, icollcb=iscoll);
  print(json.dumps(allimg, indent=1))
  # Gather count stats here (# images per pod)
  cntstat = {}
  for p in allimg:
    cnt = len( p.get("imgs", []) )
    if cntstat.get(str(cnt)): cntstat[str(cnt)] += 1
    else: cntstat[str(cnt)] = 1
  print(str(len(allimg))+ " Image stats nodes (w. 1 or more imgs)", file=sys.stderr)
  print("cntstats: "+ json.dumps(cntstat), file=sys.stderr);
  return 0

def allpods(): # args
  # cfg = args.get("cfg")
  ccnt = len(cfg.get("clusters"))
  mcpods = kubu.mc_pods(cfg)
  # Filter by ns
  nss = cfg.get("namespaces")
  if isinstance(nss, list) and len(nss): pass
  print(json.dumps(mcpods, indent=1))
  print(str(len(mcpods))+ " Kubernetes pods (on "+str(ccnt)+" clusters)", file=sys.stderr)
  return 0
def allowlist_show():
  allow = allowlist_load(cfg)
  print(json.dumps(allow, indent=1))
  print(str(len(allow))+ " Allowed items", file=sys.stderr)
# 
def check():# args
  # cfg = args.get("cfg")
  allimg = kubu.imglist(cfg, icollcb=iscoll, filter=1, debug=0); # print(json.dumps(imgidx, indent=1))
  allow = allowlist_load(cfg)
  norm = 0
  if norm:
    # Note: normaliz. MUST be done before indexing
    # allimg xform is slightly more nested (xform the inner arrays)
    for pis in allimg: xform.xform(pis.get("imgs", []), servernorm)
    #print(json.dumps(allimg, indent=1)); exit(1)
    xform.xform(allow, servernorm) ; # print(json.dumps(allow, indent=1)); # exit(1)
  # TODO: roll out / embed (for no-dep) ?
  allow_idx = indexer.index(allow, "imgbn") # OLD: image / NEW-1: imgfull NEW2 imgbn
  #print(json.dumps(allow_idx, indent=1)); # exit(1) # INDEX
  # Allow-detection. Note: Uses the whole-list
  chklvl = cfg.get("checklevel") or 1
  cres = allow_check(allimg, allow_idx, debug=0, chklvl=chklvl)
  # Populate maintainer to cres (see allow_check() for iter.) ???
  allow_idx_bn = indexer.index(allow, "bn") # By "bn" for !
  # TODO: resolve by "bn" on-the-fly in allow_report()
  #for pis in allimg:
  #  imgs = pis.get("imgs"); # pis["imgs"]
  #  for i in imgs:
  #    bn = i.get("bn") # "bn" NEW: plain bn w/o tag
  #    #iname = i.get("imgbn") # bn + tag
  #    ai = allow_idx_bn.get(bn)
  #    
  #    
  ########## Reporting (disallowed) #################
  #if cfg.get("json"): print(json.dumps(cres, indent=1))
  allow_report(cres) # TODO: pass allow_idx_bn
  return 0

def usage(msg):
  if msg: print(msg);
  print("Try ops: "); # +", ".join(ops.keys())
  for k in ops.keys():
    opn = ops[k]
    print("- "+k+" - "+ops[k]["title"]);
  sys.exit(1);
ops = {
  # {"cb":    .... , # "title": ""},
  "gencmds":   {"cb": gen_data_cmds,  "title": "Generate commands to extract cluster pod info."},
  "allpods":   {"cb": allpods,        "title": "Show raw Kubernetes pod info (merged, configured filtering applied)"},
  
  "imgstat":   {"cb": imgstat,         "title": "Show Pod image statistics (one pod to possibly many images)"},
  
  "allowlist": {"cb": allowlist_show, "title": "Dump allowlist JSON"},
  "check":     {"cb": check,  "title": "Check Pod images against allowed list"},
}
# TODO: parse opts: --all - force list all pods (ignore filtering)
if __name__ == '__main__':
  sys.argv = sys.argv[1:]
  if not len(sys.argv): usage("No subcommand/op given");
  op = sys.argv.pop(0); # x = x[1:]
  if not op: usage("No subcommand/op given");
  if not ops.get(op): usage("No subcommand "+op+" available");
  # TODO: Load config here
  # cfg = dputil.jsonload(cfgfn)
  parser = argparse.ArgumentParser(description='Pod image checker')
  parser.add_argument('index',  default=0, help='Output helper index, not the final data.') # type=ascii
  parser.add_argument('all',    default=0, help='List all pods, do not filter') # for allpods/podslist
  parser.add_argument('json',   default=0, help='Output as JSON (as applicable for action)')
  global args
  args = vars(parser.parse_args())
  args[op] = op
  args.cfg = cfg;
  ops[op]["cb"]() # args
  sys.exit(0)

