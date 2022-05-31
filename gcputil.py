# Misc GCP specific utils
# - Get / Set (Change) Project
# - Formation of "templated" command lines (with j2 ?)
# - Load,access,process ansible GCP dyn inv.
# - Generate GCP Access Keys

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

# Ensure account is set by:
# gcloud config set account $SANAME@$PROJ.iam.gserviceaccount.com first
def key_get(acct, kcfg):
  full = saname_full(acct)
  cn = 'unused'
  if not kcfg.get("expdays"): kcfg["expdays"] = 14
  cmd = "openssl req -x509 -nodes -newkey rsa:4096 -days " +
    "-keyout /tmp/priv_key.pem -out /tmp/pub_key.pem -subj '/CN=unused'"
  #run(cmd)
  # Upload public (equivalent of ssh-copy-id)
  "gcloud beta iam service-accounts keys upload /tmp/pub_key.pem "+
    "--iam-account "+full+" --project " + acct.get("projid")
  # | tee upload.txt
  # Should extract name: ... from output as private_key_id
  #jwt_make()
  
  
def saname_full(acct);
  return acct["saname"] + "@" + acct["projid"]+'.iam.gserviceaccount.com'


def jwt_make():
  jwt = {"token_uri": "https://oauth2.googleapis.com/token", "type": "service_account",
    
  };
  # "private_key_id" = # From name: ...
