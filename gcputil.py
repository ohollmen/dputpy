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
# - Orig. Google Instructions: https://cloud.google.com/iam/docs/creating-managing-service-account-keys#iam-service-account-keys-create-gcloud
# gcloud iam service-accounts keys list --iam-account=$FULL_SA_NAME --project=$PROJECT_ID --format="value(name)" \
# --filter="name~keys/${PRIV_KEY_ID} AND validBeforeTime>P${RENEW_DAYS}D"
# Shoud have "$PRIV_KEY_ID" in output
# 
# ## Notes
# - gcloud auth activate-service-account --key-file=~/service-account-key.json
# - The GCP User (e.g. serv account) may not be (does not need to be) the same user whose key is being created.

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

# Get / Generate a new key in GCP
# Params:
# - acct: Minimum: "saname":"myaccount", "projid":"myproject" to identify the account, where ...
#   - saname can be the first part before '@' of the client_email
#   - projid is the part after '@' but before fixed suffix ".iam.gserviceaccount.com"
# Ensure account is first set by:
# gcloud config set account $SANAME@$PROJ.iam.gserviceaccount.com first
# NOTE: a "native" account may also have (optional) mems:
# - "auth_uri": "https://accounts.google.com/o/oauth2/auth", (const)
# - "client_id": "127633656026938995491", (21 chars, remains const across renewed keys, identity / OAuth 2 Client ID of account by client_email)
# - "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs", (const)
# - "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/{{ client_email }}
def key_get(acct, kcfg): # , **kwargs
  # Validate mandatory
  #if not acct.get("saname", ""): return None
  #if not acct.get("projid", ""): return None
  #if not kcfg: kcfg = {}
  full = saname_full(acct)
  cn = 'unused'
  # TODO: kwargs
  if not kcfg.get("expdays"): kcfg["expdays"] = 14
  privfn = "/tmp/priv_key.pem"
  pubfn  = "/tmp/pub_key.pem"
  cmd = "openssl req -x509 -nodes -newkey rsa:4096 -days " + str(kcfg["expdays"])+ \
    " -keyout "+privfn+" -out "+pubfn+" -subj /CN=unused"
  print("Openssl CMD: "+cmd);
  res = dputil.run(cmd)
  #print( json.dumps(res) ); return
  if not os.path.exists(privfn): print("No Private key generated"); return None
  acct["private_key"] = dputil.fileload(privfn)
  if not acct["private_key"]: print("No Private key loaded"); return None
  # Unlink immediately
  
  # Upload public (equivalent of ssh-copy-id)
  cmd_up = "gcloud beta iam service-accounts keys upload "+pubfn+" "+ \
    "--iam-account "+full+" --project " + acct.get("projid")
  # Run upload and capture private_key_id from resp. See Also KEY_ID in output of command:
  # gcloud iam service-accounts keys list --iam-account=SA_NAME@PROJECT_ID.iam.gserviceaccount.com
  res = {"out": "aaa bbb name: 123456123456" } # Mock resp.
  #res = dputil.run(cmd_up)
  # Bash equivalent: export PRIVKEYID=${OUT_LINE##*/} # All after slash
  m = re.search(r'name:\s*(\w{10,})', res.get("out", "")) # Ops: MULTILINE / SINGLE LINE ?
  if m: acct["private_key_id"] = m[1]
  # | tee upload.txt
  # Should extract name: ... from output as private_key_id
  
  jwt = jwt_make(acct)
  return jwt
  
def saname_full(acct):
  # SA_NAME, PROJECT_ID (See GCP "Service Accounts")
  return acct["saname"] + "@" + acct["projid"] + '.iam.gserviceaccount.com'

# Create final / full JSON (that will be serialized)
def jwt_make(acct):
  jwt = {"token_uri": "https://oauth2.googleapis.com/token", "type": "service_account",
    #"project_id": acct.get("projid"),
  };
  # 40 Bytes
  # From name: ... of `gcloud beta iam service-accounts keys upload ...`
  if not acct.get("private_key_id") : jwt["private_key_id"] = "0000000000000000000000000000000000000000"
  else: jwt["private_key_id"] = acct.get("private_key_id") # , "0000..."
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

# Get Google spreadsheet from a spreadsheet URL.
# - authfile - JSON file with credentials to access spreadsheet
# - sheeturl - The URL of Google spreadsheet
# Sheet id / label can be passed as kwarg "sheetid"
# ```
# dputil.gsheet("authuser.json", "https://docs.google.com/spreadsheets/...")
# ```
# For Google/gspread OAuth authentication, see:
# https://docs.gspread.org/en/latest/oauth2.html
# (format and acquiry procedures same as for GCP)
def gsheet(authfile, sheeturl, **kwargs):
  import gspread
  sheetlbl = kwargs.get("sheetid") or "Sheet1"
  scope = ["https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",]
  # gspread.oauth_from_dict()
  # gc = gspread.service_account(filename=authfile) # One-step!
  # creds = Credentials.from_service_account_file(authfile, scopes=scopes)
  creds = Credentials.from_authorized_user_file(authfile, scope)
  gc = gspread.authorize(creds) # gc
  # open(title), open_by_key(key_in_url)
  sh = gc.open_by_url(sheeturl)
  wks = sh.worksheet(sheetlbl)
  # Default: AoO (?)
  data = None
  data = wks.get_all_records() # Default
  #if kwargs.get("aoa"): wks.get_all_values() # AoA
  return data
