# Misc GCP specific utils
# - Get / Set (Change) Project
# - Formation of "templated" command lines (with j2 ?)
# - Load,access,process ansible GCP dyn inv.
# - Generate GCP Access Keys
# ## GCP References
# - https://rajathithanrajasekar.medium.com/google-cloud-iam-users-extraction-across-all-projects-in-a-gcp-org-2fbe66ddc045
#   - gcloud projects get-iam-policy $projectname
# - Folders listing https://cloud.google.com/sdk/gcloud/reference/resource-manager/folders/list
#   - gcloud resource-manager folders list ...
# - 
#import dputil
import dputpy.dputil as dputil
import json
import os
import re

keyfiles = {
  "priv":"/tmp/priv_key.pem",
  "pub":"/tmp/pub_key.pem"
}

def inv_hostnames(inv, outfmt):
  hosts = inv[""]
  
  return None

# Pass "name" (displayName), ("type" ? email/), "email"
def mkchan(cfg):
  # id = cfg.get("channels", {}).get(chid);
  return None

# Pass saname, projid,
def keyfile_activate(fname):
  # "gcloud auth activate-service-account --key-file "+fname
  return

# Ensure account is set by:
# gcloud config set account $SANAME@$PROJ.iam.gserviceaccount.com first
def key_get(acct, kcfg):
  full = saname_full(acct)
  cn = 'unused'
  if not kcfg.get("expdays"): kcfg["expdays"] = 14
  privfn = "/tmp/priv_key.pem"
  pubfn  = "/tmp/pub_key.pem"
  cmd = "openssl req -x509 -nodes -newkey rsa:4096 -days " + str(kcfg["expdays"])+ \
    " -keyout "+privfn+" -out "+pubfn+" -subj /CN=unused"
  #print(cmd);
  res = dputil.run(cmd)
  #print( json.dumps(res) ); return
  if not os.path.exists(privfn): print("No Private key generated"); return None
  acct["private_key"] = dputil.fileload(privfn)
  if not acct["private_key"]: print("No Private key loaded"); return None
  # Unlink immediately
  
  # Upload public (equivalent of ssh-copy-id)
  cmd_up = "gcloud beta iam service-accounts keys upload "+pubfn+" "+ \
    "--iam-account "+full+" --project " + acct.get("projid")
  res = {"out": "aaa bbb name: 123456123456" }
  #res = dputil.run(cmd_up)
  # export PRIVKEYID=${OUT_LINE##*/} # All after slash
  m = re.search(r'name:\s*(\w{10,})', res.get("out", ""))
  if m: acct["private_key_id"] = m[1]
  # | tee upload.txt
  # Should extract name: ... from output as private_key_id
  
  jwt = jwt_make(acct)
  return jwt
  
def saname_full(acct):
  return acct["saname"] + "@" + acct["projid"] + '.iam.gserviceaccount.com'


def jwt_make(acct):
  jwt = {"token_uri": "https://oauth2.googleapis.com/token", "type": "service_account",
    #"project_id": acct.get("projid"),
  };
  # 40 Bytes
  # From name: ... of `gcloud beta iam service-accounts keys upload ...`
  if not acct.get("private_key_id") : jwt["private_key_id"] = "0000000000000000000000000000000000000000"
  else: jwt["private_key_id"] = acct.get("private_key_id")
  jwt["private_key"] = acct["private_key"]
  jwt["project_id"]  = acct.get("projid")
  jwt["client_email"] = saname_full(acct)
  return jwt

# Add Kubeproxy for particular cluster in kubeconfig
# - cname - Cluster name
# - cprox: (Full) Proxy URL
# Return kubeconfig data structure with 
def kubeproxy_add(cname, cprox, **kwargs):
  def longname():
    return "gke_"+cname+"_"+region+"_"+cname
  if not cname: return None
  if not cprox: return None
  if kwargs.get("region"): region = kwargs.get("region"); cname = longname()
  kubecfg = os.environ.get("HOME")+"/.kube/config"
  if os.environ.get("KUBECONFIG"): kubecfg = os.environ.get("KUBECONFIG")
  
  fh = open(kubecfg)
  if not fh: print("Could not open kubeconfig"); return None
  ys = list(yaml.load_all(fh, Loader=yaml.Loader))[0]
  #ys = dputil.yamlload(kubecfg, multi=1);
  # print(json.dumps(ys, indent=2)); exit(0)
  def get_cluster(it): return it.get("name") == cname
  c = list( filter(get_cluster, ys.get("clusters") ) )
  # print(json.dumps(c, indent=2)); exit(0)
  if not c: print("No cluster for "+ cname); return None
  c[0]["cluster"]["proxy-url"] = cprox
  # TODO: Optionally write back to file
  #if kwargs.get("save"): dputil.yamlwrite(ys, kubecfg)
  # yaml.dump(ys, Dumper=yaml.Dumper)
  return ys
