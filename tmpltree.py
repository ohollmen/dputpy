# dputpy template tree mapper/generator
# 
import os
import jinja2
import json
#from pathlib import Path
#import pathlib
#NON-STD:from binaryornot.check import is_binary

def init(cfg):
  # Fix tgtroot to have trailing "/"
  #if not ...: 
  # Params already embedded ? If so return w. those
  if cfg.get("params"): return
  jcfg = open(cfg.get("paramfn"), "r").read()
  cfg["params"] = json.loads(jcfg)
  return

# Binary file detection (based on stack overflow post ref'd at call location)
def is_bin(fn):
  textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
  is_binary_string = lambda bytes: bool(bytes.translate(None, textchars))
  return is_binary_string(open(fn, 'rb').read(1024))

# Extract a list of files recursively from cfg["travroot"].
# Pre-eliminates non-readble files and binary files.
# Return list of files.
# TODO: Allow list of dicts
def find_files(cfg, **kwargs):
  troot = cfg.get("travroot")
  if not troot: raise "No travroot in config"
  fnames = []
  debug = 0
  for root, dirs, files in os.walk(troot): # "."
    # root is path starting w. initial root passed to os.walk(). The root string:
    # - appears as basename in original print below (after split)
    # - always has the path passed to os.walk() prefixed to it.
    debug and print("# Found travroot subdir:" + root);
    # Subtract travroot path here (substr() or os.path.relpath() which also normalizes EXCEPT on first call)
    # ... where trailing "/./" remains (start is always nice and normalized)
    
    path = root.split(os.sep) # Gauge depth from path comps.
    bn = os.path.basename(root)
    debug and print((len(path) - 1) * '---', os.path.basename(root))
    for fn in files:
      src = root + "/" + fn
      debug and print(len(path) * '---', fn) #  ," => ", tgtpath + fn
      if not os.access(src, os.R_OK): print("NON-READABLE: "+src); continue
      # Eliminate binary right away ?
      # Seems detecting binary file is rather cumbersome in Python
      # Suggestions: https://stackoverflow.com/questions/898669/how-can-i-detect-if-a-file-is-binary-non-text-in-python
      if is_bin(src): print("BIN: "+src); continue
      #if kwargs.get("lod"): fnames.append({"": "", "": "", "":""})
      fnames.append(src)
  return fnames

def ensure_path(dn, **kwargs):
  exists = os.path.exists(dn)
  isdir = os.path.isdir(dn)
  # Check: ... As directory
  if exists and isdir: return 0
  if exists: print("PATH-ERROR: Is a file: "+dn+" expected a dir or nothing"); return 1
  if (not exists) : # or (isdir)
    if kwargs.get("debug"): print("Must create "+dn)
    try:
      #os.mkdir(dn)
      os.makedirs(dn) # parents/nested. Seems to work
      # Modern:
      #Path(dn).mkdir(parents=True, exist_ok=True)
    except OSError as error: #  
      print("PATH-ERROR: Could not create path: "+dn+" - "+str(error))
      return 1
  return 0

def map_files(cfg, fnames, **kwargs): # 
  travroot = cfg.get("travroot")
  if not travroot: raise "No travroot in config"
  tgtroot = cfg.get("tgtroot")
  if not tgtroot: raise "No tgtroot in config"
  if not fnames: raise "No files"
  p = cfg.get("params")
  # ... and object
  if not p: raise "No parameters for templating !"
  runtmpl = kwargs.get("runtmpl")
  debug = kwargs.get("debug")
  save  = kwargs.get("save")
  stats = {"except": 0, "bytecnt": 0, "filecnt": 0, "exfiles": []}
  for fn in fnames:
    relp = os.path.relpath(fn, travroot) # OLD: root, travroot
    tgtpath = tgtroot + relp # + "/"
    debug and print("# relpath: " + relp + " => tgtpath: " + tgtpath)
    # Check dir of tgtpath
    dn = os.path.dirname(tgtpath)
    #print("TGT-DIR: "+dn)
    derr = ensure_path(dn)
    if derr: continue
    # + "/" + bn
    if runtmpl:
      try:
        cont = open(fn, "r").read() # "r" OR "rb" ?
        if kwargs.get("showcont"): print(cont)
        tmpl = jinja2.Template(cont)
        ocont = tmpl.render(**p)
        debug and print("Gen'd "+str(len(ocont)) + " B of content");
        stats["bytecnt"] += len(ocont)
        stats["filecnt"] += 1
      except:
        print("Could not create content from: "+ fn + " - ...")
        stats["except"] += 1
        stats["exfiles"].append(fn)
    if save:
      debug and print("Should save output: "+tgtpath);
      debug and print(ocont);
      # Save-as
      try:
        # With "wb": TypeError: a bytes-like object is required, not 'str'
        open(tgtpath, "w").write(ocont)
      except:
        print("Error saving: "+tgtpath);
  return stats
# Example/testbed of using template tree mapper
if __name__ == "__main__":
  cfg = {"travroot": "/etc", "params": {"foo": 1}, "tgtroot": "/tmp/gentest/"}
  init(cfg)
  fnames = find_files(cfg)
  # Preferably filter files down in here to not run templating on files
  # that are not actually templates. This should not hurt anything, but
  # occasionally might trigger (e.g.) template syntax errors when template
  # parser thinks it has found a template fragment, but pattern is actually
  # just part of "other file" syntax.
  #print(json.dumps(fnames, indent=2))
  stats = map_files(cfg, fnames, runtmpl=1, save=1)
  print(json.dumps(stats, indent=2))
  print("Wrote all files to: "+cfg.get("tgtroot"));
