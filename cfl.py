#!/usr/local/bin/python3

# See
# "..." => Page Information (Always goes to /pages/viewinfo.action?pageId=... to show the page id) or
# "..." => View in Hierarchy => "Overview", "Space Details" (Space Tools, see Key/Name)
# e.g. AKey/AKeyName (Key/Name) or single token NNNN
# https://developer.atlassian.com/server/confluence/confluence-rest-api-examples/
# Child: "ancestors": [{"id": ...}]
# Update ...

# Load these essentials ONLY here
# TODO: Extract HTML
import markdown
import requests
import json
import re
# TODO: deepcopy params ?
import copy # copy.deepcopy(data)
import argparse

# Module/Pkg var for API path. Set custom per your server (see trailing comments)
# By default thee should stay relatively 
apipath = "/rest/api/content/" # Some sites: "/confluence/..."
headers = {"user-agent": "my-app/0.0.1", "Content-Type": "application/json"}
doccfg = {
  "srcfn" : "./mydoc.md",
  "spkey" : "NNN",
  "parid" : 5174,
  # Keep 0 for new doc
  "pageid" : 2439587, # 0
  "vernum" : 6,
}
# Confluence server config (example)
cflcfg = {
  "cflurl" : "https://confluence.mycompany.com",
  "creds" : {"user": "mrsmith", "passwd": "S3Crt"},
  #spkey : "NNN",
}
def loadfile(fn, parsejson):
  # Exists ...
  # if not ...: print("File "+fn+" does not exist"); return ""
  fh = open(fn, "r");
  if not fh: print("No file: "+fn+" loaded");return ""
  cont = fh.read();
  if parsejson:
    cont = json.loads(cont) # Later: return data structure
  return cont

# Convert (flat) user params (in p) to final API compatible params.
# Return None for errors
def doc2para(p, cont):
  if not p: print("No doc params passed"); return None
  para = copy.deepcopy(para_base)
  apath = apipath
  # New Doc: Must specify ancestor (non-0, must exist)
  
  if not p.get("pageid"):
    if p.get("parid"): para["ancestors"] = [{"id": p.get("parid") }]
    else: print("Must have a parent for a new document !"); return None
    #if not p.get("space", {}).get("key"): print("No Space for a new page !!!"); exit(1);
    if p.get("spkey", {}): para.get("space", {})["key"] = p.get("spkey", {})
    else: print("Must have space key (spkey) for a new document !"); return None
    if p.get("title"): para["title"] = p.get("title")
  # Update. Only pageid needed (no space, ancestor)
  else:
    pageid = p.get("pageid")
    #if pageif < 0: return None
    para["id"] = pageid
    apath += str(pageid)
    para["version"] = {}
    para["version"]["number"] = vernum
  # Set content
  para.get("body", {}).get("storage", {})["value"] = cont
  return para, apath
# print(md)



para_base = {
  "type":"page",
  "title":"My First Dynamic codument",
  #"ancestors": [{"id": ...}]
  "space": {"key": "" }, # doccfg.get("spkey")
  "body":{
    "storage": {
      "value": "", # cont
      "representation": "storage"
    }
  }
}

if __name__ == "__main__":
  # Load main config
  #cfg = loadfile("./cfl.conf.json", 1)
  #if not cfg: print("No Config loaded"); exit(1)
  print("Work in progress");exit(1);
  # Grab params from CL
  parser = argparse.ArgumentParser(description='Confluence Ext-Doc manager')
  # required=False,
  parser.add_argument('--pageid',  default="", help='Page / Document ID (for existing page)')
  parser.add_argument('--parid',  default="", help='Parent Page / Document ID (for new page)')
  parser.add_argument('--spkey',  default="", help='Page / Document Space Key')
  parser.add_argument('--vernum',  default="", help='Page / Document Version Number')
  parser.add_argument('--title',  default="", help='Page / Document Title')
  args = vars(parser.parse_args())
  print(json.dumps(args, indent=2));
  p = args
  fn = "README.md"
  cont = loadfile(fn, 0)
  if not cont: print("Could not load document file: "+fn); exit(1)
  # Handle .md, .html
  # if re.match(r'\.md$', fn)
  #print("Handling MD (by conversion): "+ fn);
  cont = markdown.markdown(cont)
  #elif re.match(r'\.html$', fn)
  print("Handling HTML doc (as-is): "+ fn)
  para, apipath = doc2para(p, cont)
  cfg = cflcfg # TEST
  creds = cfg.get("creds")
  auth = requests.auth.HTTPBasicAuth(creds["user"], creds["passwd"])
  print("Send to: "+apipath)
  print( json.dumps(para, indent=2) )
  exit(0)
  ##### HTTP / REST #################
  
  # New page (POST)
  if not pageid:
    # data={'key': 'value'}
    r = requests.post(cflurl + apipath, headers=headers, auth=auth, data=json.dumps(para))
    #foo = 89
  # Update. (PUT)
  else:
    r = requests.put(cflurl + apipath, headers=headers, auth=auth, data=json.dumps(para))
    foo = 99
  print(r.text); 