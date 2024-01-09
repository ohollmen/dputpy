#!/usr/local/bin/python3

# See
# "..." => Page Information (Always goes to /pages/viewinfo.action?pageId=... to show the page id) or
# "..." => View in Hierarchy => "Overview", "Space Details" (Space Tools, see Key/Name)
# e.g. AKey/AKeyName (Key/Name) or single token NNNN
# https://developer.atlassian.com/server/confluence/confluence-rest-api-examples/
# Child: "ancestors": [{"id": ...}]
# Update ...

# Local (MD) and Confluence document instance specific parameters
# mdfn  - Markdown document to send to confluence. Handy when working continuously on same document. Should be normally passed from CL
#         by --mdfn
# pageid - Confluence document id. Handy when working continuously on same doc.
# Note: Both these params (outside the above mentione use-case) can also be dangerous to keep in static configuration as
#  wrong document in confcluence can be owerwritten with (wrong) local markdown document.
# After finishing a document authoring session with mdfn and/or pageid in config it is recommended to 
# 
# parid - Parent document. Handy thing to keep in config when working with multiple docs under same parent doc and creating
#      new documents frequently.
# cflurl - Server URL (with port, but no trailing slash) to Confluence server (top level, no URl paths included).
# spkey - Cofluence Document space key.
# 

# Load these essentials ONLY here
# TODO: Extract HTML
# ## Testing
# python3 dputpy/cfl.py new --spkey NNN --parid 700706251 --mdfn test.md --title "Test Document"
# python3 dputpy/cfl.py update --pageid 735414552 --mdfn test.md
import markdown
import requests
import json
import re
# TODO: deepcopy params ?
import copy # copy.deepcopy(data)
import argparse
import os
import sys # argv
import markdownify
import bs4

# Module/Pkg var for API path. Set custom per your server (see trailing comments)
# By default thee should stay relatively 
apipath = "/rest/api/content/" # Some sites: "/confluence/..."
headers = {"user-agent": "my-app/0.0.1", "Content-Type": "application/json"}
# Example (JSON) config. Copying this to cfl.conf.json will give you template to start with.
# mdfn (todo: srcfn for HTML)
doccfgXX = {
  "mdfn" : "./mydoc.md",
  "cflurl": "https://confluence.mycomp.com",
  "spkey" : "NNN",
  "parid" : 5174,
  # Keep 0 for new doc
  "pageid" : 2439587, # 0
  "vernum" : 6,
  "creds": {
    "user": "",
    "pass":"",
  }
}
# Confluence server config (example)
cflcfg = {
  "cflurl" : "https://confluence.mycompany.com",
  "creds" : {"user": "mrsmith", "pass": "S3Crt"},
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
# Let p["pageid"] drive the use-cases create new / update existing.
# Return None for errors
def doc2para(p, cont):
  if not p: print("No doc params passed"); return None
  para = copy.deepcopy(para_base)
  apath = apipath # Local modded version
  # New Doc: Must specify ancestor (non-0, must exist)
  
  if not p.get("pageid"):
    if p.get("parid"): para["ancestors"] = [{"id": p.get("parid") }]
    else: print("Must have a parent id (parid) for a new document !"); return None, None
    #if not p.get("space", {}).get("key"): print("No Space for a new page !!!"); exit(1);
    if p.get("spkey", {}): para.get("space", {})["key"] = p.get("spkey", {})
    else: print("Must have space key (spkey) for a new document !"); return None
    if p.get("title"): para["title"] = p.get("title")
  # Update. Only pageid needed (no space, ancestor)
  #      "message": {
  #        "key": "You can't change an existing page's space.",
  #        "args": []
  #      }
  #    },
  #    {
  #      "message": {
  #        "key": "You need to include the title to update a page.",
  #        "args": []
  #      }
  # TODO: Retrieve old document (by pageid) to
  # 1) fill in title (.title) 2) get the spkey .space.key (Also: .container.key) 3) Inc. version (.version.number)
  else:
    pageid = p.get("pageid")
    #if pageif < 0: return None
    para["id"] = pageid
    apath += str(pageid)
    para["version"] = {}
    if p.get("vernum"): para["version"]["number"] = p.get("vernum")
    if p.get("title"): para["title"] = p.get("title")
    else: del para["title"] # Do NOT change title
    if p.get("spkey", {}): para.get("space", {})["key"] = p.get("spkey", {})
  # Set content
  para.get("body", {}).get("storage", {})["value"] = cont
  return para, apath
# print(md)


def cflpage_read(p):
  pageid = p.get("pageid")
  if not pageid: print("No pageid to get a page from confluence"); return;
  global apipath
  url = p.get("cflurl")+apipath+""+pageid+"?expand=body.storage"
  print("Call:"+url);
  creds = p.get("creds")
  auth = requests.auth.HTTPBasicAuth(creds["user"], creds["pass"])
  r = requests.get(url, headers=headers, auth=auth)
  #print(r.text)
  rj = json.loads(r.text)
  if not isinstance( rj, dict ): print("Response not in JSON format. Raw resp: "+r.text);
  ht = rj.get("body").get("storage").get("value")
  #print(json.dumps(rj, indent=2)) # All of JSON
  soup = bs4.BeautifulSoup(ht, features="html.parser")
  print(soup.prettify())
  # If ... HTML-to_MD
  md = markdownify.markdownify(ht)
  print("\n\nMD:\n"+md);
  return

# Validate filename, return content
def mdfn_validate(p):
  fn = p.get("mdfn") # or "README.md"
  if not fn: print("Must pass markdown filename (--mdfn)"); exit(1)
  if not os.path.isfile(fn): print("No MD file by name '"+fn+"'"); exit(1)
  cont = loadfile(fn, 0)
  if not cont: print("Could not load MD file: '"+fn+"'"); exit(1)
  return cont
  
def cfldoc_create_or_update(p):
  fn = p.get("mdfn")
  cont = mdfn_validate(p)
  if not cont: usage("No content gotten from: "+ fn);
  # TODO: Handle .md, .html
  if re.search(r'\.md$', fn):
    print("Handling MD (by conversion): "+ fn);
    cont = markdown.markdown(cont)
  elif re.search(r'\.html$', fn):
    print("Handling HTML doc (as-is): "+ fn)
  else: usage("File suffix is neither .md or .html - check your content.")
  #  Convert all to Cfl REST
  para, apipath = doc2para(p, cont)
  if not para: usage("No REST params created")
  if not apipath: usage("No apipath available");
  # cfg = cflcfg # TEST
  creds = cfg.get("creds")
  auth = requests.auth.HTTPBasicAuth(creds["user"], creds["pass"])
  print("Send to: "+p.get("cflurl")+apipath)
  print( json.dumps(para, indent=2) )
  #exit(0)
  ##### HTTP / REST #################
  
  # New page (POST)
  if not p.get("pageid"):
    # data={'key': 'value'}
    r = requests.post( cfg.get("cflurl") + apipath, headers=headers, auth=auth, data=json.dumps(para))
    #foo = 89
  # Update. (PUT)
  else:
    r = requests.put( cfg.get("cflurl") + apipath, headers=headers, auth=auth, data=json.dumps(para))
    foo = 99
  # TODO: parse, reformat in pretty ...
  rj = json.loads(r.text)
  if not isinstance( rj, dict ): print("Response not in JSON format. Raw resp: "+r.text);
  print(json.dumps(rj, indent=2))
  exit(0)


# For Create/Update
para_base = {
  "type":"page",
  "title":"My First Dynamic Document",
  #"ancestors": [{"id": ...}]
  "space": {"key": "" }, # doccfg.get("spkey")
  "body":{
    "storage": {
      "value": "", # cont
      "representation": "storage"
    }
  }
}
def usage(msg):
  print(msg)
  print("Try one of subcommands: "+ ' '.join( ops.keys() ) )
  exit(1)

ops = {"new": cfldoc_create_or_update, "update": cfldoc_create_or_update, # "conv": ..., "help": ..., "cfl2md": ...,
  "cflhtml": cflpage_read, # "md2html": ...
}
if __name__ == "__main__":
  # Load main config
  cfgfn = "./cfl.conf.json"
  cfg = loadfile(cfgfn, 1)
  if not cfg: usage("No Config loaded")
  print(json.dumps(cfg, indent=2));
  #print("Work in progress");exit(1);
  # Grab params from CL
  parser = argparse.ArgumentParser(description='Confluence Ext-Doc manager')
  # required=False,
  parser.add_argument('--pageid',  default="", help='Page / Document ID (for existing page)')
  parser.add_argument('--parid',  default="", help='Parent Page / Document ID (for new page)')
  parser.add_argument('--spkey',  default="", help='Page / Document Space Key')
  parser.add_argument('--vernum',  default="", help='Page / Document Version Number')
  parser.add_argument('--title',  default="", help='Page / Document Title')
  parser.add_argument('--mdfn',  default="", help='Markdown filename')
  if len(sys.argv) < 2: usage("Pass subcommand as first arg.")
  op = sys.argv.pop(1); # x = x[1:]
  if not op: usage("No subcommand given (as first arg)")
  if not ops.get(op): usage("No subcommand '"+op+"' available");
  
  args = vars(parser.parse_args())
  print(json.dumps(args, indent=2));
  p = args
  # TODO: Transfer/merge CL args to cfg.
  for k in args:
    if p.get(k): cfg[k] = p[k]
  if not cfg.get("cflurl"): usage("Need cflurl");
  ops[op](cfg)
  #cflpage_read(cfg)
  #
  exit(0);

