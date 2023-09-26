import os
import jinja2
import json
#NON-STD:from binaryornot.check import is_binary

def init(cfg):
  # Fix tgtroot to have trailing "/"
  #if not ...: 
  # Params already embedded ? If so return w. those
  if cfg.get("params"): return
  jcfg = open(cfg.get("paramfn"), "r").read()
  cfg["params"] = json.loads(jcfg)
  return

def is_bin(fn):
  textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
  is_binary_string = lambda bytes: bool(bytes.translate(None, textchars))
  return is_binary_string(open(fn, 'rb').read(1024))

def find_files(cfg):
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
      if not os.access(src, os.R_OK): print("NOT readable: "+src); continue
      # Eliminate binary right away ?
      # Seems detecting binary file is rather cumbersome in Python
      # Suggestions: https://stackoverflow.com/questions/898669/how-can-i-detect-if-a-file-is-binary-non-text-in-python
      if is_bin(src): print("BIN: "+src); continue
      fnames.append(src)
  return fnames

def map_files(cfg, fnames):
  travroot = cfg.get("travroot")
  if not travroot: raise "No travroot in config"
  tgtroot = cfg.get("tgtroot")
  if not tgtroot: raise "No tgtroot in config"
  if not fnames: raise "No files"
  p = cfg.get("params")
  # ... and object
  if not p: raise "No parameters for templating !"
  runtmpl = 1
  for fn in fnames:
    relp = os.path.relpath(fn, travroot) # OLD: root, travroot
    tgtpath = tgtroot + relp # + "/"
    print("# relpath: " + relp + " => tgtpath: " + tgtpath);
    # + "/" + bn
    if runtmpl:
      #try:
      cont = open(fn, "r").read() # "r" OR "rb" ?
      print(cont)
      tmpl = jinja2.Template(cont)
      ocont = tmpl.render(**p)
      print("Gen'd "+str(len(ocont)) + " B of content");
      #except:
      #  
    # Check dir of tgtpath
    dn = os.path.dirname(tgtpath)
    print("TGT-DIR: "+dn)
    if (not os.path.exists(dn)) or (os.path.isdir(dn)):
      print("Must create "+dn)
    # try:
    #  os.mkdir(dn)
    #except: OSError as error:
    #  print("Could not create ...")
    #if not
    # Save-as open()
if __name__ == "__main__":
  cfg = {"travroot": "/etc", "params": {"foo": 1}, "tgtroot": "/tmp/"}
  init(cfg)
  fnames = find_files(cfg)
  #print(json.dumps(fnames, indent=2))
  map_files(cfg, fnames)
