#!/usr/bin/env python3
import dputpy.dputil as dputil
import os
import json
cmds = {
  ".svn": "svn status -u",
  ".git": "git status"
}

basedn = '.'; # f"/home/{}"

def vc_dirs(basedn):
  files = os.listdir(basedn)
  varr = []
  for fn in files:
    absfn = f"{basedn}/{fn}"
    print(f"File: {absfn}")
    # Also .exists()
    if os.path.isdir(absfn): # and ..
      vcdt = "" # VC dir type
      vcp = {"path": absfn, "vcdt": ""}
      if   os.path.isdir(f"{absfn}/.svn"): vcp["vcdt"] = ".svn"
      elif os.path.isdir(f"{absfn}/.git"): vcp["vcdt"] = ".git"
      if vcp["vcdt"]: pass # print(f"{absfn} Is VC directory for {vcp['vcdt']}")
      else: print(f"Warning: Non-VC dir: {absfn}")
      varr.append(vcp)
    elif os.path.isfile(absfn): pass
  return varr

varr = vc_dirs(basedn)
print(json.dumps(varr, indent=2))
