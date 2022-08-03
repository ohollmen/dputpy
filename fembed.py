# fembed is a module to create files with files embedded either into
# YAML or JSON format. fembed avoids the time/effort spent on the
# tedious and error prone escaping/indenting/editing of file when pasting
# file content into YAML (or JSON).
# Files subject to this kind of file-embedding are (e.g.):
# - Ansible copy task with content
# - Kubernetes config maps and secrets "data" section (binaryData not supported)
# - FCOS (Fedore CoreOS) Ignition storage.files section
# This module focuses only on the array-of-objects (list-of-dicts)
# containing embedded files
# The central vocabulary of fembed
# - path: absolute (or relative) path of file to create (Ansible: dest)
# - content: Content of the file (FCOS: "contents", K8S: the value of filename key)
# - mode: File **octal** (include starting perm mode 

import dputpy.dputil as dputil
import yaml
import json
import copy
import os # os.path.basename, dirname
import pathlib
import hashlib

calcmd5 = 0

testarr = [
  {"path": "/etc/passwd", "mode": "0755", },
  {"path": "/etc/timezone", "mode": "0755", },
  #{"path": "/etc/docker/key.json", "mode": "0755", },
];

# Add a file into
def addfile(flist, lpath, **kwargs):
  node = {"path": lpath}
  if kwargs.get("mode"):
    node["mode"] = kwargs.get("mode")
  # Override path with kwargs["dpath"] if different from path
  if kwargs.get("dpath"):
    node["path"] = kwargs.get("dpath")
  # See if explicit content is given (for e.g. short files like /etc/hostname)?
  # if kwargs.get("content"):
  #   node["content"] = kwargs.get("content")
  # else: # ...
  node["content"] = dputil.fileload(lpath)
  if kwargs.get("md5") or calcmd5:
    node["md5"] = hashlib.md5(node["content"].encode('utf-8')).hexdigest()
    # TypeError: Unicode-objects must be encoded before hashing
    #node["md5"] = hashlib.md5(node["content"]).hexdigest()
  flist.append(node)

# Transform into the final data structure for particular backend
# - flist: list of files with standard properties
# - btype: ans,kube,ign
def fmap_out(flist, btype):
  kubmap = {}
  dlist = []
  # TODO: Clone / deepcopy original items ?
  for f0 in flist:
    f = copy.deepcopy(f0)
    if btype == 'ans':
      f["dest"] = f["path"]; del f["path"]
      dlist.append(f);
    if btype == 'ign':
      f["contents"] = f["content"]; del f["content"]
      dlist.append(f);
    if btype == 'kube':
      kubmap[f["path"]] = f["content"]
  if btype == 'kube': return kubmap
  return dlist

def ensuredir(path):
  if not os.path.exists(path) or not os.path.isdir(path):
    mode = 0o755
    #os.mkdir(path, mode) # Only one step
    os.makedirs(path, mode=mode) # Creates intermed ...
  return

# Note: for now this has to be done before fmap_out() as
# items have been modded in it
def fmap_write(flist, dpath):
  if not dpath: dpath = "/tmp/"
  ensuredir(dpath)
  for f in flist:
    fullpath = dpath + f["path"]
    pathonly = os.path.dirname(fullpath)
    ensuredir(pathonly)
    dputil.filewrite(f["content"], fullpath)
  print("Wrote to: "+dpath);
  return

# read stored map back
#def fmap_read(flist, spath):
#  for f in flist:
#    fullpath = spath + f["path"]
#    dputil.fileread(fullpath)

if __name__ == "__main__":
  print("Test additions ...")
  calcmd5 = 1
  cwd = os.getcwd()
  testarr.append({"path": cwd+"/tdata/dict.yaml"})
  flist = []
  # Test addfile()
  for ti in testarr:
    addfile(flist, ti["path"], **ti)
  #fmap_write(flist, "/tmp/write-test/"); exit()
  testyaml = "/tmp/flist.yaml"
  print("Writing as YAML ("+testyaml+")");
  dputil.yamlwrite(flist, testyaml)
  print("Loading back YAML");
  flist = dputil.yamlload(testyaml)
  
  #exit(1)
  #flist = fmap_out(flist, "ans")
  print(json.dumps(flist, indent=2))
  #print(yaml.dump(flist, Dumper=yaml.Dumper))
