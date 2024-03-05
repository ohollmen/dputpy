# dputpy template tree mapper/generator
# Traverse and collect files in a directory tree as templates to generate content for.
# Load a (global, singular) set of parameters to fill in templates with
# (passing parameters to Jinja2 render() ) and capture the "expanded" (tempalted)
# content for each files. Save and store the templated files into a separate
# directory tree.
# ## Config format
# Following parameters are supported for config
# - travroot - Source root directory for source template traversal
# - tgtroot - Target directory to save templated content to
# - paramfn - filename for file to use as parameters for Jinja 2 templating
# - check - Perform misc checks for e.g. target dir presence (etc.)
# - debug - Turn on verbose runtime debug messages (for troubleshooting)
# - excsuff - List of suffixes to exclude from templating give as dictionary
#             with keys reflecting suffixes and values set to (any) true value)
# ## Features
# - Skip binary files as non-templateable
# - Always skip .git directories as sub-tree to NOT template
# ## Limitations
# - All collected files (left after skip logig above) will be treated as
#   templates. Files with template fragments '{{' or failed data lookups in
#   template fragments may trigger an exception)
# ## TODO
# - Create more sophisticated exclude mechanisms (by file suffix, dir tree, ...).
# - Change excsuff to more user friendly list and ONLY internally convert to
#   dict-index
import os
import jinja2
import json
import yaml
import re # For suffix matching
#from pathlib import Path
#import pathlib
#NON-STD:from binaryornot.check import is_binary
import shutil

def init(cfg):
  # Fix tgtroot to have trailing "/"
  #if not ...: 
  # Params already embedded ? If so return w. those
  if cfg.get("params"): pass # return
  #jcfg = open(cfg.get("paramfn"), "r").read()
  #cfg["params"] = json.loads(jcfg)
  else: cfg["params"] = loadcfg(cfg.get("paramfn"));
  if not cfg.get("params"): raise "Missing params (from main config 'params' or file by 'paramfn')"
  if cfg.get("check") and not cfg.get("tgtroot"): raise "No destination path 'tgtroot' give (with check on)"
  # Ensure empty suffixmap (or not of type 
  if not cfg.get("excsuff") or (type(cfg.get("excsuff")) != dict):
    cfg["excsuff"] = {}
  return
# Load JSON (or YAML) config file.
# Simply detect popular suffixes from end of fn (using str.endswith()).
# Test (in py console): import tmpltree; d = tmpltree.loadcfg("tdata/dict.yaml")
# Note: This ONLY works for single-doc YAML files (No '---' or single '---').
# Return data(structure) in JSON file
def loadcfg(fn):
  if not os.path.isfile(fn): raise "File '"+fn+"' does not exist"
  cont = open(fn, "r").read()
  if not cont: raise "No config content gotten from '"+fn+"'"
  cfg = None
  if fn.endswith(".json"): cfg = json.loads(cont)
  elif fn.endswith( (".yaml", ".yml")):
    cfg = yaml.safe_load(cont)
    # y = yaml.load_all(data, Loader=Loader) # multidoc ????
  if not cfg: raise "No config data (dict) gotten from config file '"+fn+"'"
  return cfg

# Binary file detection (based on stack overflow post ref'd at call location)
def is_bin(fn):
  textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
  is_binary_string = lambda bytes: bool(bytes.translate(None, textchars))
  return is_binary_string(open(fn, 'rb').read(1024))

# Extract a list of files recursively from cfg["travroot"].
# Pre-eliminates non-readble files and binary files. Also skip anything in ".git" (including dir itself).
# Return list of files.
# TODO: Allow list of dicts
def find_files(cfg, **kwargs):
  troot = cfg.get("travroot")
  if not troot: raise "No travroot in config"
  fnames = []
  debug = cfg.get("debug")
  for root, dirs, files in os.walk(troot): # "."
    # root is path starting w. initial root passed to os.walk(). The root string:
    # - appears as basename in original print below (after split)
    # - always has the path passed to os.walk() prefixed to it.
    debug and print("# Found travroot subdir:" + root);
    # Subtract travroot path here (substr() or os.path.relpath() which also normalizes EXCEPT on first call)
    # ... where trailing "/./" remains (start is always nice and normalized)
    
    path = root.split(os.sep) # Gauge depth from path comps.
    if ".git" in path:
      debug and print("GIT dir (or dir/file under .git): "+root);
      continue
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

def explicit_files(cfg, **kwargs):
  fnames = cfg.get("files")
  if not fnames: return None
  if not len(fnames): return None
  # Assume always relative names, relative to cfg.travroot
  fnames = list( map(lambda fn: cfg.get("travroot") + fn, fnames) )
  return fnames

# Helper for use-case where an non-templated tree is copied to destination, followed by
# overlaying a different (but structuarlly similar dir tree) templated dir tree.
# This does only the copy-part.
# Take source and dest root (paths) from same config members as other use-cases.
# uses ensure_path()
# TODO: Consider shutil.copytree(src, dest, dirs_exist_ok=True) 3.8+ (for dirs_exist_ok)
# Note: distutils.dir_util.copy_tree(src, dst, ...) (otherwise fit) will be removed in 3.12
def copyfiles(cfg, files, **kwargs):
  fnames = find_files(cfg)
  stats = {}
  try:
    stats = map_files(cfg, fnames, runtmpl=0, copyonly=1) # No templating !!!
  except:
    print("Error copying files from "+cfg.get("")+" to "+cfg.get("")+" !")
  return stats

# Ensure that target path directory exists before generating and storing
# files (and creating sub-directories) under it.
# Return true values 1 and up for errors (e.g. dir is a file or creation fails).
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
# Map list of templates files from source tree (travroot) to 
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
  copyonly  = kwargs.get("copyonly")
  stats = {"except": 0, "bytecnt": 0, "filecnt": 0, "exfiles": [],
  "excsuffcnt": 0, "copycnt": 0}
  excsuff = cfg.get("excsuff") or {}
  for fn in fnames:
    # Extract relative path to map/append to tgtroot
    relp = os.path.relpath(fn, travroot) # OLD: root, travroot
    tgtpath = tgtroot + relp # + "/"
    debug and print("# relpath: " + relp + " => tgtpath: " + tgtpath)
    # Check dir of tgtpath
    dn = os.path.dirname(tgtpath)
    #print("TGT-DIR: "+dn)
    derr = ensure_path(dn)
    if derr: continue
    suff = "" # None stringifies to 'None'
    ocont = ""
    # Extract file suffix for advanced skip-logic
    # os.path.splitext(fpath)[-1].lower() )
    # OR import pathlib; pathlib.Path('file.yml').suffix == '.yml'
    # OR bn.split(".")[-1] OR m = re.search('\.\w+$', fn) # ... ,flags=re.IGNORECASE
    #suff = relp.split(".")[-1]
    m = re.search('\.(\w+)$', fn)
    if m and m[1]: suff = m[1]
    debug and print("Suffix: '"+str(suff)+"' ("+relp+")");
    # Need import shutil. ensure_path() already executed !!!
    if copyonly:
       shutil.copyfile(fn, tgtpath) # Returns tgtpath ?
       stats["copycnt"] += 1 # Update stats
       continue
    #else: print("No copyonly present")
    # + "/" + bn
    if runtmpl: # and 
      try:
        cont = open(fn, "r").read() # "r" OR "rb" ?
	#ocont = None # No need to declare
        if kwargs.get("showcont"): print(cont)
        # Skip templating for particular suffix, store original content
        if suff and excsuff.get(suff): ocont = cont; stats["excsuffcnt"] += 1
        else:
          tmpl = jinja2.Template(cont)
          ocont = tmpl.render(**p)
          debug and print("Gen'd "+str(len(ocont)) + " B of content");
        stats["bytecnt"] += len(ocont)
        stats["filecnt"] += 1
      except Exception as err:
        print("Error in Template expansion: Could not create content from: "+ fn + " - "+str(err) )
        stats["except"] += 1
        stats["exfiles"].append(fn)
    # else:
    #   
    if runtmpl and save:
      debug and print("Should save output: "+tgtpath);
      debug and print(ocont);
      # Save-as
      try:
        # With "wb": TypeError: a bytes-like object is required, not 'str'
        open(tgtpath, "w").write(ocont)
      except Exception as err:
        print("Error saving: '"+tgtpath+ "' Error: "+ str(err) );
  return stats
# Example/testbed of using template tree mapper
if __name__ == "__main__":
  cfgfn = os.environ["TMPLTREE_CONFIG"] or "./tmpltree.conf.json"
  # Example config
  cfg = {"travroot": "/etc", "params": {"foo": 1}, "tgtroot": "/tmp/gentest/",
    "check": 1, "excsuff": {"load": 1, "properties": 1, "md": 1}}
  if os.path.isfile(cfgfn) or os.path.isfile("./tmpltree.conf.yaml"):
    try:
      cfg = loadcfg(cfgfn)
    except:
      print("Config file "+cfgfn+"found, but could not be loaded");exit(1)
  init(cfg)
  # Choose files
  fnames = cfg.get("files")
  if fnames: fnames = explicit_files(cfg)
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
