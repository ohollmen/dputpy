# Groups of GCP Commands (as parametrized templates)
# Keep as separate lists for ease of handling a grouped commands context.

# TODO: make use of deepcopy to create instance specific copy of expanded/ filled-in set

# GCP Loadbalancers
# List snapshots
# gcloud compute snapshots list
# Create disk from snapshot
# https://cloud.google.com/compute/docs/disks/restore-snapshot
# Create disk (from SN) to attach to an existing instance
# gcloud compute disks create DISK_NAME --size=120 --source-snapshot=SNAPSHOT_NAME --type=pd-ssd
# gcloud compute instances attach-disk INSTANCE_NAME --disk DISK_NAME
# gcloud compute instances detach-disk --disk=my-disk (Or --device-name=my-device) --disk-scope
# gcloud compute instances create VM_NAME --source-snapshot=BOOT_SNAPSHOT_NAME --boot-disk-size=BOOT_DISK_SIZE \
#   --boot-disk-type=BOOT_DISK_TYPE --boot-disk-device-name=BOOT_DISK_NAME
# ## Collecting template set vars
# https://unix.stackexchange.com/questions/13466/can-grep-output-only-specified-groupings-that-match
# ```
# grep -oP '^(tmpls_\w+)' dputpy/gcpcmds.py
# ```
# ## TODO:
# Instead of module-globals, group sets of templates to (e.g. for tmpls_uni)
# tgrps["uni"] = [ ....
import copy # copy.deepcopy(data)
import jinja2
import json
import dputpy.dputil as dputil
import re
#
tmpls_idx = {}
#TODO: tgrps = {}
# Set project, VM stop, VM start, VM meta backup, dns change
# { "id": "", "title": "", "tmpl": ""},
tmpls_uni = [
  { "id": "proj_set", "title": "Set Project Context",
    "tmpl": "gcloud config set project {{ projid }}" },
  { "id":"vmi_stop", "title": "Stop VM instance",
    "tmpl": "gcloud compute instances stop {{ vmname_d }} --project {{ projid }} --zone {{ zone_b }}" },
  { "id": "vmi_start", "title": "Start VM Instance",
    "tmpl":"gcloud compute instances start {{ vmname_d }} --project={{ projid }} --zone={{ zone_b }}" },
  { "id": "vmi_meta_tofile", "title": "Store VM Meta info (for later/emergency reference)",
    "tmpl": "gcloud compute instances describe {{ vmname_d }} --format json --project {{ projid }} --zone {{ zone_b }} > {{ vmname_d }}.dr_backup.{{ isodate }}.json"
  },
  { "id": "vmi_meta", "title": "Output VM Meta info",
    "tmpl": "gcloud compute instances describe {{ vmname_d }} --format json --project {{ projid }}{% if zone_b %} --zone {{ zone_b }}{% endif %}" },
  { "id":"vmi_list", "title":"List VMs of a Project.",
    "tmpl":"gcloud compute instances list --format json --project {{ projid }}" },
  { "id": "dns_update", "title": "Update DNS record",
  "tmpl": "gcloud dns record-sets update {{ servdns }}.{{ domainname }} --rrdatas '{{ newip }}' --type {{ rectype }} " + \
     "--ttl={{ dnsttl }} --zone=projects/{{ projid }}/managedZones/{{ domainzone }} --project={{ projid }}" },
  # Also: folders/$FOLDER_ID --folder ...
  { "id": "audit_logs", "title": "List Project Audit Log",
     "tmpl": "gcloud logging read 'logName : projects/{{ projid }}/logs/cloudaudit.googleapis.com' --format json --project {{ projid }}" },
    # Seems either full URL or MI basename will work
  { "id":"mi_desc", "title":"Describe single machine image in detail.",
    "tmpl":"gcloud compute machine-images describe --format json --project {{ projid }} {{ miname }}"
  
  }

]

tmpls_mirec = [
  #{ "id": "vmi_stop", "title": "Stop VM Instance",
  #"tmpl": "gcloud compute instances stop {{ vmname_d }} --zone {{ zone_b }}" },
  #{ "id": "vmi_mi_gen", "title": Backup ? This is out of date anyways, so no need 
  #out += "gcloud compute machine-images create {{ vmname_d }}-{{ isodate }}-dr --source-instance {{ vmname_d }} --zone {{ zone_b }}";
  { "id": "vmi_unlock", "title": "Release VM Deletion Protection",
  "tmpl": "gcloud compute instances update {{ vmname_d }} --no-deletion-protection --project {{ projid }} --zone {{ zone_b }}" },
  { "id": "vmi_del", "title": "Delete Old VM (by its original name) (also supports: --keep-disks all|boot|data)",
  "tmpl": "gcloud compute instances delete {{ vmname_d }} --delete-disks all --project {{ projid }} --zone {{ zone_b }}" },
  

  
  { "id": "mi_list", "title": "Choose recent / latest machine image for recovery (Consider: | grep selfLink )", # Note: See the format of --source-machine-image for next command. 
  # Note: OLD: --format json  + | grep selfLink. Stop doing this (has fluff/garbage), use --format 'get(name)' to get scalar, directly suitable normalized value.
  # Addl Note:--format 'get(selfLink)' works too, but givew full https://... URL. The next template is only looking for 'name' (for the end)
  "tmpl": "gcloud compute machine-images list --format 'get(name)' --filter='name:{{ vmname_s }}' --limit=1  --sort-by='~creationTimestamp' --project {{ projid }}", # | grep selfLink
  "outvar": "MI_NAME"},
  { "id": "vmi_restore_mi", "title": "Create VM from MI backup", # Note: the machine to bring up may not exist and cannot be looked up to derive e.g zone
  # TODO: destinat. zone B - derive from hnode, which is derived from (selfLink (has apiprefix) ? basename in "name", could use as srcimg )
  # projects/myproj-vpc/regions/us-west1/subnetworks/mine-usw1
  # TODO: Consider --resource-policies
  "tmpl": "gcloud beta compute instances create {{ vmname_d }} " + \
   " --project {{ projid }} --zone {{ zone_b }} " + \
   " --subnet projects/{{ netprojid }}/regions/{{ region_b }}/subnetworks/{{ destsubnet }} " + \
   " {% if extipaddr %}--address '{{extipaddr}}'{% else %}--no-address{% endif %} --private-network-ip {{ ipaddr }} --deletion-protection --source-machine-image  {{ apiprefix }}projects/{{ projid }}/global/machineImages/{{ srcimg }}",
   },
]

tmpls_ssrec = [
  #{ "id":"vmi_stop", "title": "Stop VM instance",
  #"tmpl": "gcloud compute instances stop {{ vmname_d }} --zone {{ zone_b }}" }, #; out += "\n"
  { "id":"vmi_disk_det", "title": "Detach disk from old/existing VM",
  # Can use --disk (name, equal to VM name by conv.) OR --device-name (avail in ansdi). Use --disk, because it MUST be avail for delete op
  # Note: on bad proj:  The project property must be set to a valid project ID, [...] is not a valid project ID.
  # Boot disk: Disk [persistent-disk-0 ] is not attached to instance [...] in zone [...].
  "tmpl": "gcloud compute instances detach-disk {{ vmname_d }} --disk {{ diskname_d }} --project {{ projid }} --zone {{ zone_b }}" },
  { "id":"disk_del", "title": "Delete old disk",
  # NOTE: Rely on same naming between disk and VM (!?, see above p = {...}). This is a blessing as ansdi does NOT have disk name (only deviceName)
  "tmpl": "gcloud compute disks delete '{{ diskname_d }}' --quiet --project {{ projid }} --zone {{ zone_b }}" },
  #### Region/Env A Snapshot
  
  { "id":"ss_list_recent", "title": "Choose recent / latest snapshot (Latest first, | grep '\"name\"' for brevity)",
  # github-us-east1-b* NOT supp: --zone {{ zone_a }}
  # Note: See notes on compute machine-images list (Add --format 'get(name)', Elim. grepping).
  "tmpl": "gcloud compute snapshots list --format 'get(name)' --filter='name:{{ vmname_s }}' --sort-by '~creationTimestamp' --limit 1 --project {{ projid }} ", # | grep '\"name\"'
  "outvar":"SS_NAME"},
  { "id":"disk_ss_create", "title": "Extract disk from VM Snapshot",
  # ...of A (to dest zone - zone of B). Disk name by conv. same as VM. Shapshot policy should come from policy of B / region B
  # Policies can be found from Snapshots => SS Schedules. Note: THIS does NOT have device name param. Cannot use --project (is embedded in --source-snapshot path) Manual says it can.
  # OLD: {{ apiprefix }}projects/{{ projid_a }}/zones/{{ zone_a }}/snapshots/{{ snapname }}
  # https://cloud.google.com/compute/docs/disks/scheduled-snapshots
  "tmpl": "gcloud compute disks create {{ vmname_d }} --project {{ projid }} --zone {{ zone_b }} --type pd-ssd"  +\
    " --resource-policies '{{ rpols }}' --source-snapshot {{ apiprefix }}projects/{{ projid_a }}/global/snapshots/{{ snapname }}" },
  { "id": "vmi_disk_att", "title": "Re-attach disk to VM", # (VM Name == Disk Name by conv.) --device-name dr-gitlab-vm-test. Note: added --device-name
  "tmpl": "gcloud compute instances attach-disk {{ vmname_d }} --disk {{ vmname_d }} --boot --device-name {{ devname }} --project {{ projid }} --zone {{ zone_b }}" },
]

tmpls_k8s_status = [
  
]

tmpls_k8s_dkill = [
  { "id":"kub_pod_del", "title": "Delete Pod(s)",
    "tmpl":"kubectl delete pod {{ podname }} -n {{ namespace }}"},
]
# Note: Looping through this we could check "when" property => statement
tmpls_k8s_dscale = [
  #{ "id":"kub_depl_status", "title": "Get pods and deployments status",
  #  "tmpl":"kubectl get pods -n {{ namespace }}; kubectl get deployments -n {{ namespace }} -o wide"},
   { "id":"kub_pod_depl_check", "title": "Check Pods, Deployments and Ingress",
    "tmpl": "kubectl get pods -n {{ namespace }} ; kubectl get deployments -n {{ namespace }} -o wide ; kubectl get ing -n {{ namespace }}"},
  { "id":"kub_depl_scale", "title": "Scale deployment",
    "tmpl":"kubectl scale --replicas={{ replicacnt }} deployment/{{ deplname }} -n {{ namespace }}"},
  
 
]
# https://cloud.google.com/kubernetes-engine/docs/how-to/api-server-authentication
tmpls_k8s_envinit = [
  { "id":"gcp_act_sa", "title": "Activate Service account",
    "tmpl": "gcloud auth activate-service-account --key-file={{ jwtfn }}" },
  # Follow by kubectl cluster-info (also --zone)
  { "id":"gcp_clus_creds", "title": "Get GKE Cluster Credentials",
    "tmpl": "gcloud container clusters get-credentials {{ cluster }} --project {{ project }} --region {{ region }} --internal-ip"},
  # Get region location:
  { "id":"gcp_clus_loc", "title": "Cluster Region-Location",
    "tmpl": "gcloud container clusters list --project {{ project }} --filter 'name={{ cluster }}' --format 'value(location)'"},
  { "id":"gcp_config_region", "title": "Set Region-Location",
    "tmpl": "gcloud config set compute/region {{ region }}"},

]
# Add property grp (label) to template.
# TODO: Additionally add to index !!!
def set_parent(arr, parlbl):
  for it in arr:
    it["grp"] = parlbl
    tmpls_idx[it.get("id", "")] = it;
  
def init():
  # Index all sets ? Create "out" member to all ?
  # tmpls_uni, tmpls_mirec, tmpls_ssrec, tmpls_k8s, tmpls_k8s_envinit
  set_parent(tmpls_uni, "uni")
  set_parent(tmpls_mirec, "mirec")
  set_parent(tmpls_ssrec, "ssrec")
  set_parent(tmpls_k8s_status, "k8s_status")
  set_parent(tmpls_k8s_dkill, "k8s_dkill")
  set_parent(tmpls_k8s_dscale, "k8s_dscale")
  set_parent(tmpls_k8s_dscale, "k8s_dkill")
  set_parent(tmpls_k8s_envinit, "k8s_envinit")
  # Populate: tmpls_idx = {}
  #print("TMPL IDX: "+json.dumps(tmpls_idx, indent=2));
  return

# Get a template by id from a known array passed in kwrags["arr"]
def tmpl_get(id, **kwargs):
  # From an array - sequential find ...
  arr = kwargs.get("arr")
  if arr and isinstance(arr, list):
    m = list(filter(lambda t: t.get("id") == id, arr))
    if not m: return None
    return m[0]
  return tmpls_idx.get(id) # Note: set_parent currently puts stuff to tmpls_idx


# Run command expanded (to out), check if post-processing is needed.
# Use input from fillin_set where "out" is already filled in
def run():
  for t in tset:
    # "onerror"
    ret = dputil.run(t.get("out"))
    if ret["rc"]: print("Error running "+ t.get("out")); return;
    #if t.get("ctype", "").index('json') > -1: # Throws error on no match !
    if re.search(r"json", t.get("ctype", "")): # Or just "fmt" (like for dputil.run()
      t["jdata"] = json.loads(ret.get("out"))
    # See if post-run handler is registered. TODO: Allow string ?
    if t.get("postrun"): t.get("postrun")(ret, t)
  return

# Fill in set of (list sequenced) templates with common parameters.
# Run templating fill-in on single/individual template level to be as normalized as possible.
# Example of templating and turning to command sequence:
#     out = gcmds.commandseq( gcmds.fillin_set(tset, p) )
# Returns a copy of original set with "out" member filled in with template params.
def fillin_set(tset, p, **kwargs):
  tset = copy.deepcopy(tset)
  for t in tset:
    template = jinja2.Template(t["tmpl"])
    #t["out"] += ("# "+ t["title"]+"\n"+t["tmpl"] + "\n")
    t["out"] = template.render(**p)
    ### OUTVAR ####
    ov = t.get("outvar")
    #print("OUTVAR: "+str(ov));
    if ov: t["out"] = ov+"=`"+t["out"]+"`"
    # TODO: fillin(t, p) # Check deepcopy() state before ena !!!
    t["errchk"] = "if [ $? -ne 0 ]; then echo 'Error during op: "+t.get("title")+"'; exit 1; fi\n"
  #if kwargs.get(""):
  #if kwargs.get("str"): return
  return tset

# Fill in single template item
def fillin(t, p, **kwargs):
  t = copy.deepcopy(t)
  t["out"] = "" # Empty to be apendable
  if kwargs.get("title"): t["out"] = "# "+t.get("title")+"\n"
  template = jinja2.Template(t["tmpl"])
  t["out"] += template.render(**p)
  ### OUTVAR ####
  ov = t.get("outvar")
  #print("OUTVAR: "+str(ov));
  if ov: t["out"] = ov+"=`"+t["out"]+"`"
  #if kwargs.get("errchk"):
  t["errchk"] = "if [ $? -ne 0 ]; then echo 'Error during op: "+t.get("title")+"'; exit 1; fi\n"
  return t

# Convert pre-rendered template set into a command sequence (string).
def commandseq(tset, **kwargs):
  out = kwargs.get("initstr", "")
  outarr = []
  #print("ERRCHK=" + str( kwargs.get("errchk", "N/A") ) );
  for t in tset:
    out += ("# "+ t["title"]+"\n"+t["out"] + "\n")
    if kwargs.get("errchk"): out += t.get("errchk", "") # Add error check on explicit request
    # Case array - ONLY include "out"
    #outarr.append(t["out"]);
  return out

# pushd dputpy; python3 gcpcmds.py; popd
# python3 dputpy/gcpcmds.py > 
# Aggregate all to single array (init groups in "grp"), dump as JSON.
if __name__ == "__main__":
  #print("Templates as JSON ...");
  init()
  # Concat multiple arrays together ( grep ^tmpls_ gcpcmds.py )
  arr = [tmpls_uni, tmpls_mirec, tmpls_ssrec, tmpls_k8s, tmpls_k8s_envinit]
  arrc = []
  # NOT: arrc.append(sub)
  for sub in arr:
    #for it in sub: it["parent"] = retrieve_name(sub)
    arrc += sub
  print( json.dumps(arrc, indent=2) )


