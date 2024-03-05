#!/usr/local/bin/python3
# ## Getting ansible  dynamic inventory (config: "invfn")
# ansible-inventory --list > inventory_all.json
# # TODO
# - Possibly rename e.g. vmname_d to a/b convention.
import re
import json
import dputpy.dputil as dputil
import dputpy.ansdi as adi
import dputpy.svs as svs
import dputpy.gcpcmds as gcmds
import jinja2
import os # For env
import sys
#import copy

# See linetboot(for some of the orig. conventions "./serv_host.json")

# Old block of ...
#invfn = dputil.jsonload(mcfg["invfn"])
#adi.new(invfn)
## Access ?
#hmap = adi.hmap_get()
##gcmds.init() # Optional
#servs = dputil.jsonload(mcfg["svsfn"]) # OLD: svs, svs_fn
##print(json.dumps(hmap, indent=2));



# swtype = Swich type: host, lb
# https://cloud.google.com/dns/docs/records
# Implementation expects the DNS records to exist in DNS and only updates them (does not create)
def dns_change(s, mcfg):
  lbips = s.get("halbip", [])
  newip = lbips[1] # From dest
  p = {
    "dnsttl": mcfg.get("dnsttl"), "rectype": "A",
    "newip": newip,
    # get fallback OR initial value from projid ???
    "projid": mcfg.get("netprojid") # extend([p, s], keys=[""]) if not set
  }  
  p["domainname"] = s.get("domainname") # Used for $hn.$domainname (see fallback to global below)
  p["domainzone"] = s.get("domainzone") # NEW (used in GCP path-notation)
  #NOT: p["projid"] = s.get("projid") # OK as Fallback ?
  if (not p["domainname"]): p["domainname"] =  mcfg["domainname"]
  if not p.get("projid"): p["projid"] = "PROJID" # Lookup !!
  p["servdns"] = s.get("servdns")
  if not p.get("servdns"): p["servdns"] = "SERVDNSNAME" # Service DNS name
  # create => update rrdatas=
  #out = "gcloud dns record-sets update {{ servdns }}.{{ domainname }} --rrdatas '{{ newip }}' --type {{ rectype }} " + \
  #   "--ttl={{ dnsttl }} --zone=projects/{{ projid }}/managedZones/{{ domainzone }} --project={{ projid }}" # ; 
  tn = gcmds.tmpl_get("dns_update", arr=gcmds.tmpls_uni)
  if not tn or not tn.get("tmpl"): print("Error getting template"); exit(1)
  template = jinja2.Template(tn.get("tmpl"))
  out = template.render(**p);
  if mcfg.get("errchk"): out += "\nif [ $? -ne 0 ]; then echo 'Error during op: "+tn.get("title")+"'; exit 1; fi\n"
  #print(out)
  return out

def depls_shift(s, mcfg):
  
  return

# Recover VM from Machine Image. Assumes:
# - source and target MI/VM are in same project
# - netprojid: 1) global, serv, 
# TODO: How do we know that (netproject +) region + subnetname combo exists
# https://cloud.google.com/sdk/gcloud/reference/compute/networks/subnets/list
# gcloud compute networks subnets list --project ...
# gcloud compute url-maps list --project ...
# gcloud compute forwarding-rules list --project ...
def mi_restore(s, mcfg):
  if not isinstance(s, dict): print("Service not in dict"); exit(1)
  sh = svs.vm_get_idx(s, 0)
  dh = svs.vm_get_idx(s, 1)
  p2 = {
    #"projid": s.get("projid"),
    # "srcimg": s.get("haimg") # Does not scale to rev.
    "srcimg": sh.get("hname") + '-' + mcfg.get("isodate") # Always Reg. A (source). OLD: dputil.isotime(date=1)
  }
  p = extend([ gentpara(s), p2 ])  
  # Order: netprojid in
  # OLD: s.get("hasubnet") 
  p["destsubnet"] = svs.subnet_dr(s) or  "SUBSUB" # Lookup from ... networkInterfaces[0].subnetwork.selfLink (name/region/selfLink)
  p["ipaddr"] = adi.netif(dh, ipaddr=1); # NOT: s.get("halbip", [])[1] MUST Come from HOST (B)
  #print("NETADDR(dest): "+p["ipaddr"]);
  p["netprojid"] = mcfg.get("netprojid")
  if not p["netprojid"]: p["netprojid"] = s.get("netprojid") # Hosuld prioritize service netprojid !!!
  if not p["netprojid"]: p["netprojid"] = s.get("projid") # "NETPROJECT" # Project of VMs
  out = gcmds.commandseq( gcmds.fillin_set(gcmds.tmpls_mirec, p) , errchk=mcfg.get("errchk") )
  #print(out)
  return out

# Create common params (svs?)
def gentpara(s): # ,mcfg
  sh = svs.vm_get_idx(s, 0)
  dh = svs.vm_get_idx(s, 1)
  if not sh: print("Did not find source host (A) "+ s.get("hapair")[0]);
  if not dh: print("Did not find dest host (B) "+ s.get("hapair")[1]);
  p = { "vmname_s": s.get("hapair")[0], "vmname_d": s.get("hapair")[1],
    "zone_a":   sh.get("zone"),
    "zone_b":   dh.get("zone"),
    "region_a": sh.get("region"),
    "region_b": dh.get("region"),
    "projid_a": sh.get("project"),
    "projid_b": dh.get("project"),
    "projid":   s.get("projid"), # compare to sh/dh ? if a == b ?
    # "apiprefix": "https://compute.googleapis.com/compute/v1/",
    "apiprefix": "https://www.googleapis.com/compute/v1/",
    "isodate" : dputil.isotime(date=1), # TODO: From mcfg
  }
  return p

# Extend first dict by the keys of latters
def extend(dicts, **kwargs):
  # Possibly pop ?
  bdict = dicts.pop(0) # Removes
  if not bdict: bdict = {}
  # Check list
  #if not isinstance(dicts, list): return None
  for d in dicts:
    for k in d.keys(): # TODO: variants like if not yet in bdict (only_if_no_in_base)
      if d[k]: bdict[k] = d[k] # k is bound to exist (per d.keys())
  return bdict

# Produce a *set* of commands for Snap restore
def ss_restore_disk(s, mcfg):
  if not isinstance(s, dict): print("Service not in dict"); exit(1)
  if not isinstance(mcfg, dict): print("Main config not in dict"); exit(1)
  sh = svs.vm_get_idx(s, 0)
  dh = svs.vm_get_idx(s, 1)
  if not sh: print("Did not find source host (A) "+ s.get("hapair")[0]);
  if not dh: print("Did not find dest host (B) "+ s.get("hapair")[1]);
  # Get dest disk device name (B) from ADI
  destdevname = adi.hnode_disk_prop(dh, "deviceName")
  sss = s.get("snapschds")[1] # Dest/B Snapshot schedule
  #print("Dest node "+dh.get("hname")+" deviceName: "+destdevname+"\n");
  snapname = "REPLACE_W_SNAPSHOT_NAME"
  p2 = {    
    #OLD: "snapname": s.get("snapname"), # Env A snapshot, For now from s
    "diskname_d": s.get("hapair")[1],
    "snapname": "REPLACE_W_SNAPSHOT_NAME",
    
    "rpols": sss,
    #PREPOP:"apiprefix": "https://compute.googleapis.com/compute/v1/",
    "devname": destdevname
  }
  p = extend([ gentpara(s), p2 ])
  #print(json.dumps(p, indent=2)) ; exit()
  if not p.get("devname"): p["devname"] = p.get("diskname_d")
  # This "scalar solution" (global env. var, or global config member) is questionable as we could have many services w. "ss"
  #env_ssn = os.environ.get("SNAPSHOT_NAME") # SS Name from ENV
  #if env_ssn: p["snapname"] = env_ssn
  # OR - mainconfig.snapshots (by service name given in)
  #if s.get("snapname"): p["snapname"]: s.get("snapname") # Somewhat okay
  #template = jinja2.Template(out); out = template.render(**p)
  out = gcmds.commandseq( gcmds.fillin_set(gcmds.tmpls_ssrec, p), errchk=mcfg.get("errchk") )
  #print(out)
  return out

# Restore K8S deployment in reg. B
# Use fillin(t, p) for ad-hoc purposes here
def kubdepl_restore(s, mcfg):
  clctx = mcfg.get("k8scmd")+" -c "+s.get("clusters", [])[1]+"\n" # Create cmd to login to cluster context
  logintmpl = {"id": "k8s_login", "title": "Login to Cluster", "tmpl": mcfg.get("k8scmdtmpl", "") }
  poddeltmpl = gcmds.tmpl_get("kub_pod_del")
  if not poddeltmpl: print("No tmpl by kub_pod_del !"); exit(1)
  # appinit() inited the templates, but we'll add this dynamically created one
  gcmds.tmpls_k8s_dscale.insert(0, logintmpl)
  gcmds.tmpls_k8s_dscale.append(gcmds.tmpl_get("kub_pod_depl_check"))
  p = {
    "k8scmd":   mcfg.get("k8scmd"),
    "replicacnt": 0, # ,
    "cluster":   s.get("clusters", [])[0],
    "namespace": s.get("namespace", "UNKNOWN-NS"),
    "deplname":  s.get("deplname", "UNKNOWN-DEPL"),
    "podname":   s.get("podname", "UNKOWN_POD"),
  }
  out = "# Disable old deployment (and pod) if cluster is still up (not a real disaster).\n"
  out += gcmds.commandseq( gcmds.fillin_set(gcmds.tmpls_k8s_dscale, p) , errchk=mcfg.get("errchk") )
  out += gcmds.fillin(poddeltmpl, p, title=True)["out"] +"\n"
  out += "# Exit cluster\nexit\n\n"; out += "# Enable deployment in recovery region/location.\n"
  #p2 = copy.deepcopy(p)
  # For secondary change cluster and replicacnt
  p["cluster"] = s.get("clusters", [])[1]
  p["replicacnt"] = s.get("replicacnt", 1) # Def. 1
  out += gcmds.commandseq( gcmds.fillin_set(gcmds.tmpls_k8s_dscale, p) , errchk=mcfg.get("errchk") )
  out += "# Exit cluster\nexit\n"
  return out

# Do (e.g.) template initializations (once only) here, so that app can
# handle multiple mi/ss recoveries.
def appinit():
  gcmds.init() # Init toolkit !
  # Here we insert(at off=0) and append to tmpl arr to be utilized as de-facto
  # Add SS commodity ops
  gcmds.tmpls_ssrec.insert(0, gcmds.tmpl_get("vmi_stop", arr=gcmds.tmpls_uni))
  gcmds.tmpls_ssrec.insert(0, gcmds.tmpl_get("vmi_meta", arr=gcmds.tmpls_uni))
  #gcmds.tmpls_ssrec.insert(0, gcmds.tmpl_get("proj_set", arr=gcmds.tmpls_uni))
  gcmds.tmpls_ssrec.append(gcmds.tmpl_get("vmi_start", arr=gcmds.tmpls_uni))
  ####### MI Template inits (add commodity ops) ####
  gcmds.tmpls_mirec.insert(0, gcmds.tmpl_get("vmi_stop", arr=gcmds.tmpls_uni))
  gcmds.tmpls_mirec.insert(0, gcmds.tmpl_get("vmi_meta", arr=gcmds.tmpls_uni))
  #gcmds.tmpls_mirec.insert(0, gcmds.tmpl_get("proj_set", arr=gcmds.tmpls_uni))
  gcmds.tmpls_mirec.append(gcmds.tmpl_get("vmi_start", arr=gcmds.tmpls_uni))
  # K8S depl. Use .extend() to concat()
  # gcmds.tmpls_k8s_dscale.insert(0, gcmds.tmpl_get(""))
  #gcmds.tmpls_k8s_dscale.append(gcmds.tmpl_get("kub_pod_depl_check")) # Add status or whole
  #print(gcmds.tmpls_k8s_dscale) # Debug dump
  return

def dr_info(servs):
  iso = dputil.isotime(date=1)
  # print("# DR on "+iso+"\n"); # TODO: envname_a to envname_b
  #global mcfg; global dom; 
  #print(json.dumps(servs, indent=2)); print(json.dumps(hmap, indent=2)); exit(1);
  # DNS Change on Service. Return chunk of title/command.
  def serv_dns_change(s):
    global mcfg
    lbips = s.get("halbip", "") # In flag role
    #if s.get("resttype"): return # Skip restore types ?
    # TODO: Check (for each item) if recovery already done ???
    if lbips:
      return "# "+s.get("title")+ "\n" + dns_change(s, mcfg)
  # MI / Snap
  imgsections = []
  butr = {"mi":"Machine image", "snap":"Snapshot (w. Disk)", "k8sdepl":"Kubernetes Deployment", "": "Unknown/Invalid"}
  ####### MAIN LOOP ########
  for s in servs:
    lbips = s.get("halbip", "") # In flag role
    haimg = s.get("haimg", "")
    resttype = s.get("resttype");
    # print("# "+s.get("title"));
    # MI or SS or K8S Depl. restore (resttype = restoration type)
    
    if resttype:
      docitem = {}
      buname = butr.get(resttype, "")
      if not buname: print("Recovery type "+resttype+" is not supported"); exit(1);
      #print("## "+s.get("title")+" Machine bring-up of type: "+buname+"\n"); # On tmpl !
      docitem["heading"] = s.get("title")+" Machine bring-up of type: "+buname+"";
      #print("Instantiate "+s.get("title")+" from "+buname+" of A\n") # + haimg
      docitem["intro"] = "Instantiate "+s.get("title")+" from "+buname+" of A"
      #OLD:print("Set project context and back up info (old VM B)\n\ngcloud config set project "+s.get("projid")+"")
      ######
      #dh = svs.vm_get_idx(s, 1)
      #dh["isodate"] = iso
      #tmpl = "gcloud compute instances describe --format json --zone {{ zone }} {{ hname }} > {{ hname }}.dr_backup.{{ isodate }}.json\n\n"
      #template = jinja2.Template(tmpl)
      #print( template.render(**dh) );
      if resttype == 'mi':        docitem["cmds"] = mi_restore(s, mcfg);
      elif resttype == 'snap':    docitem["cmds"] = ss_restore_disk(s, mcfg)
      elif resttype == 'k8sdepl': docitem["cmds"] = kubdepl_restore(s, mcfg)
      #p = gentpara(s)
      #template = jinja2.Template("gcloud compute instances start {{ vmname_d }}  --zone={{ zone_b }}\n\n")
      #print( template.render(**p) );
      imgsections.append(docitem)
  #OLD: print("# DNS Changes\n"); # On tmpl !
  dnschanges = [];
  # TODO: Retain "t" structure here to have title avail for error message
  for s in servs:
    dnsch = serv_dns_change(s)
    if not dnsch: continue
    dnschanges.append(dnsch)
  tpara = { "imgsections": imgsections, "dnschanges": dnschanges, "mcfg": mcfg }
  return tpara

# 
def usage(msg):
  if msg: print(msg);
  print("Try one of subcommands: " + ", ".join( ops.keys() ) )
  exit(1);
def gendoc(mcfg, servs):
  if mcfg.get("op") == "script":  mcfg["tmplfn"] = "./dr_script.sh.j2"; mcfg["errchk"]=True # Shell script
  tpara = dr_info(servs)
  #print(json.dumps(tpara, indent=2)) # DEBUG
  #NOT: tmplcont = dputil.fileload(mcfg["tmplfn"])
  #exit(1);
  if not mcfg["tmplfn"]: usage("No template given in config ('tmplfn')")
  tmpl = dputil.tmpl_load(mcfg["tmplfn"])
  if not tmpl: usage("No template loaded from: "+mcfg["tmplfn"]+"")
  out = tmpl.render(**tpara)
  print(out);

ops = {"doc": gendoc, "script": gendoc}
if __name__ == '__main__':
  rev = 0 # OR TODO: from CLI
  rev_env = os.environ.get("DR_REVERSE")
  if rev_env: rev = 1
  if sys.argv.count("--rev"): rev = 1
  ### 
  appinit() # gcmds.*
  mcfg_fn = "./dr.prod.conf.json"
  mcfg = dputil.jsonload(mcfg_fn)
  if not mcfg: usage("No main config loaded (from: "+mcfg_fn+")");
  if (not rev) and mcfg.get("reverse"): rev = 1
  mcfg["reverse"] = rev # Set for e.g. templating
  if not mcfg.get("invfn"): usage("No inventory in main cfg."); # exit(1)
  if not mcfg.get("svsfn"): usage("No services file in main cfg."); #exit(1)
  # New blok of inits
  invfn = dputil.jsonload(mcfg["invfn"])
  if not invfn: usage("No inverntory filename expresed in config ('invfn')!");
  adi.new(invfn)
  # Access ?
  hmap = adi.hmap_get()
  if not hmap: usage("No host map gotten from Ansible dynamic inventory.")
  #gcmds.init() # NOT Optional, but done in appinit()
  servs = dputil.jsonload(mcfg["svsfn"]) # OLD: svs, svs_fn
  if not servs: usage("No serices model gotten from (JSON) file: "+mcfg["svsfn"]+"");
  #print(json.dumps(hmap, indent=2));
  # Cont ...
  adi.hmap_init(hmap) # if ???: usage("Dyn. inv. host map init failed !")
  # Late enough that all other inits are completed (e.g. rev takes effect here)
  svs.init(servs, mcfg, rev) # if ???: usage("")
  #print(json.dumps(servs, indent=2)); exit(1);
  op = None # "doc"
  if len(sys.argv) > 1: op = sys.argv[1]
  if not op: usage("No subcommand passed !");
  if not ops.get(op): usage("Subcommand "+op+" not suported !")
  mcfg["op"] = op
  ops.get(op)(mcfg, servs)
  
