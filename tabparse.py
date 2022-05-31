#!/usr/bin/python3
# Parse tabular file
# See Also:
# https://docs.python.org/3/library/pipes.html
# https://docs.python.org/2/library/subprocess.html#module-subprocess
import json
import pipes
import os
import re
#import pytest

#import pipes
#t = pipes.Template() # fh = t.open('pipefile', 'w')
# from subprocess import Popen, PIPE

# TODO: create "canned" profiles to parse files or command pipes by

flds_p = ["uname","pass","uid","gid","gecos","home","shell"]
flds_g = ["gname","pass","gid","mems"]
flds_m = ["rsc","_on","mountat","_type","fstype", "opts"]

def parsetab(fname, attrs, **kwa):
  if not fname: raise "parsetab: No filename"
  fh = None
  # NOTE: recommended: subprocess module
  # NOTE: b makes a difference in opening (for python 3)
  if kwa.get("cmd"): fh = os.popen(fname, "r")
  # pipe = Popen("cmd", shell=True, bufsize=bufsize, stdout=PIPE).stdout
  else: fh = open(fname, "r")
  if not fh: raise "No fh"
  sep = kwa.get("sep") # Default ?
  if not sep: raise "No sep"
  arr = []
  proc = kwa.get("proc")
  isre = kwa.get("re")
  for l in fh.readlines():
  #while l = fh.readline():
    l = l.rstrip()
    # print("line: "+l);
    if isre: r = re.split(sep, l)
    else: r = l.split(sep)
    ent = {}
    i = 0
    for a in attrs: ent[a] = r[i]; i = i + 1
    if proc: proc(ent)
    arr.append(ent);
  return arr

# Delete scrap keys.
# Also: del e["key"], but throws KeyError
def mountclean(e):
  e.pop("_on")
  e.pop("_type")
# Split group mems to array
def mk_mems(e):
    ml = e["mems"].split(',')
    if ml and ml[0] == '': e["mems"] = []
    else: e["mems"] = ml

# TODO: methods like has(), cnt_gt
def dirlist(path):
  arr = os. listdir(path)
  print(json.dumps(arr, indent=2));
  return arr

# TODO: Move to a test_*.py file 
#def test_groups():
  
if __name__ == "__main__":
  
  arr = parsetab("/etc/passwd", flds_p, sep=':')
  print("FILE"+json.dumps(arr, indent=2))
  arr2 = parsetab("cat /etc/passwd", flds_p, sep=':', cmd=1)
  print("PIPE"+json.dumps(arr2, indent=2))
  
  arr_g = parsetab("cat /etc/group", flds_g, sep=':', cmd=1, proc=mk_mems)
  print("GROUPS"+json.dumps(arr_g, indent=2))
  dirlist("/tmp")
  #for l in fh.readlines():
  #  print(l);
