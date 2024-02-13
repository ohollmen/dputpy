#!/usr/local/bin/python3
# ## Getting ansible  dynamic inventory (config: "invfn")
# ansible-inventory --list > inventory_all.json
import re
import json
import dputpy.dputil as dputil
import dputpy.ansdi as adi
import dputpy.svs as svs
import dputpy.gcpcmds as gcmds
import jinja2
import os # For env
import sys

# See linetboot(for some of the orig. conventions "./serv_host.json")

# Old block of ...
#invfn = dputil.jsonload(mcfg["invfn"])
#adi.new(invfn)
## Access ?
#hmap = adi.hmap_get()
##gcmds.init() # Optional
#servs = dputil.jsonload(mcfg["svsfn"]) # OLD: svs, svs_fn
##print(json.dumps(hmap, indent=2));



# swtype = Stich type: host, lb
# https://cloud.google.com/dns/docs/records
def dns_change(s, mcfg):
  lbips = s.get("halbip", [])
  newip = lbips[1] # From dest
  p = {
    "dnsttl": mcfg.get("dnsttl"), "rectype": "A",
    "newip": newip,
    # get fallback OR initial value from projid ???
    "projid": mcfg.get("netprojid") # extend([p, s], keys=[""]) if not set
  }  
  p["domainname"] = s.get("domainname")
  p["domainzone"] = s.get("domainzone") # NEW
  #NOT: p["projid"]    = s.get("projid") # OK Fallback ?
  if (not p["domainname"]): p["domainname"] =  mcfg["domainname"]
  if not p.get("projid"): p["projid"] = "PROJID" # Lookup !!
  p["servdns"] = s.get("servdns")
  if not p.get("servdns"): p["servdns"] = "HOST" # Service DNS name
  # create => update rrdatas=
  #out = "gcloud dns record-sets update {{ servdns }}.{{ domainname }} --rrdatas '{{ newip }}' --type {{ rectype }} " + \
  #   "--ttl={{ dnsttl }} --zone=projects/{{ projid }}/managedZones/{{ domainzone }} --project={{ projid }}" # ; 
  tn = gcmds.tmpl_get("dns_update", arr=gcmds.tmpls_uni)
  if not tn or not tn.get("tmpl"): print("Error getting template"); exit(1)
  template = jinja2.Template(tn.get("tmpl"))
  out = template.render(**p); #out += ""
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
  out = gcmds.commandseq( gcmds.fillin_set(gcmds.tmpls_mirec, p) )
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
  # Get dest disk device name (B)
  destdevname = adi.hnode_disk_prop(dh, "deviceName")
  sss = s.get("snapschds")[1] # Dest/B Snapshot schedule
  #print("Dest node "+dh.get("hname")+" deviceName: "+destdevname+"\n");
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
  env_ssn = os.environ.get("SNAPSHOT_NAME") # SS Name from ENV
  if env_ssn: p["snapname"] = env_ssn
  # OR - mainconfig.snapshots (by service name given in)
  #if s.get()
  
  #out = ""
  # Target VM/disk (B): Stop, Detach disk and delete it (get name from output: )
  ## out += "Stop instance, detach it's disk and delete it"; out += "\n\n"
  # OLD: Template inits
  
  
  #for t in gcmds.tmpls_ssrec: out += ("# "+ t["title"]+"\n"+t["tmpl"] + "\n")
  #template = jinja2.Template(out)
  #out = template.render(**p)
  out = gcmds.commandseq( gcmds.fillin_set(gcmds.tmpls_ssrec, p) )
  #print(out)
  return out

# Do (e.g.) template initializations (once only) here, so that app can
# handle multiple mi/ss recoveries.
def appinit():
  # Add SS commodity ops
  gcmds.tmpls_ssrec.insert(0, gcmds.tmpl_get("vmi_stop", arr=gcmds.tmpls_uni))
  gcmds.tmpls_ssrec.insert(0, gcmds.tmpl_get("vmi_meta", arr=gcmds.tmpls_uni))
  gcmds.tmpls_ssrec.insert(0, gcmds.tmpl_get("proj_set", arr=gcmds.tmpls_uni))
  gcmds.tmpls_ssrec.append(gcmds.tmpl_get("vmi_start", arr=gcmds.tmpls_uni))
  ####### MI Template inits (add commodity ops) ####
  gcmds.tmpls_mirec.insert(0, gcmds.tmpl_get("vmi_stop", arr=gcmds.tmpls_uni))
  gcmds.tmpls_mirec.insert(0, gcmds.tmpl_get("vmi_meta", arr=gcmds.tmpls_uni))
  gcmds.tmpls_mirec.insert(0, gcmds.tmpl_get("proj_set", arr=gcmds.tmpls_uni))
  gcmds.tmpls_mirec.append(gcmds.tmpl_get("vmi_start", arr=gcmds.tmpls_uni))
  return

def dr_info(servs):
  iso = dputil.isotime(date=1)
  # print("# DR on "+iso+"\n"); # TODO: envname_a to envname_b
  ###### INIT ########
  # Populate img names
  #global mcfg
  #global dom
  
  
  #print(json.dumps(servs, indent=2)); exit(1); # DUMP
  #print(json.dumps(hmap, indent=2)) # DUMP
  # DNS Change on Service
  def serv_dns_change(s):
    global mcfg
    lbips = s.get("halbip", "") # In flag role
    #if s.get("resttype"): return # Skip restore types ?
    if lbips:
      #print() 
      #print("- Switch DNS to LB IP: "+lbips[1] )
      # TODO: Check if recovery already done ???
      return "# "+s.get("title")+ "\n" + dns_change(s, mcfg)
  
  
  # MI / Snap
  imgsections = []
  ####### MAIN LOOP ########
  for s in servs:
    lbips = s.get("halbip", "") # In flag role
    haimg = s.get("haimg", "")
    resttype = s.get("resttype");
    # print("# "+s.get("title"));
    # MI or SS restore (resttype = restoration type)
    
    if resttype:
      butr = {"mi":"Machine image", "snap":"Snapshot (w. Disk)", "": "Unknown/Invalid"}
      docitem = {}
      buname = butr.get(resttype)
      #print("## "+s.get("title")+" Machine bring-up of type: "+buname+"\n");
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
      if resttype == 'mi':
        docitem["cmds"] = mi_restore(s, mcfg);
      #print("Instantiate "+s.get("title")+" from latest snapshot of A");
      elif resttype == 'snap':
        docitem["cmds"] = ss_restore_disk(s, mcfg)
      #p = gentpara(s)
      #template = jinja2.Template("gcloud compute instances start {{ vmname_d }}  --zone={{ zone_b }}\n\n")
      #print( template.render(**p) );
      imgsections.append(docitem)
    #if pair:
    #  #if not pair: print("No DNS switch info"); continue
    #  print("!!!!!!!!");
    #  dns_flip(s, "host")
    #  #print(json.dumps(s))
  #print("# DNS Changes\n");
  dnschanges = [];
  for s in servs:
    dnsch = serv_dns_change(s)
    if not dnsch: continue
    dnschanges.append(dnsch)
  tpara = { "imgsections": imgsections, "dnschanges": dnschanges, "mcfg": mcfg }
  return tpara
# 
def usage(msg):
  if msg: print(msg);
  #", ".join( ops.keys() ) 
  exit(1);
ops = {}
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
  if not mcfg.get("invfn"): usage("No inventory in main cfg."); # exit(1)
  if not mcfg.get("svsfn"): usage("No services file in main cfg."); #exit(1)
  # New blok of inits
  invfn = dputil.jsonload(mcfg["invfn"])
  if not invfn: usage("No inverntory filename expresed in config ('invfn')!");
  adi.new(invfn)
  # Access ?
  hmap = adi.hmap_get()
  if not hmap: usage("No host map gotten from Ansible dynamic inventory.")
  #gcmds.init() # Optional
  servs = dputil.jsonload(mcfg["svsfn"]) # OLD: svs, svs_fn
  if not servs: usage("No serices model gotten from (JSON) file: "+mcfg["svsfn"]+"");
  #print(json.dumps(hmap, indent=2));
  # Cont ...
  adi.hmap_init(hmap) # if ???: usage("Dyn. inv. host map init failed !")
  # Late enough that all other inits are completed (e.g. rev takes effect here)
  svs.init(servs, mcfg, rev) # if ???: usage("")
  #print(json.dumps(servs, indent=2)); exit(1);
  tpara = dr_info(servs)
  #print(json.dumps(tpara, indent=2)) # DEBUG
  #NOT: tmplcont = dputil.fileload(mcfg["tmplfn"])
  #exit(1);
  if not mcfg["tmplfn"]: usage("No template given in config ('tmplfn')")
  tmpl = dputil.tmpl_load(mcfg["tmplfn"])
  if not tmpl: usage("No template loaded from: "+mcfg["tmplfn"]+"")
  out = tmpl.render(**tpara)
  print(out);
