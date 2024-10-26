#!/usr/bin/env python3
# # Generate output by Jinja 2 templating from a parameter-model.
# Implements a simple free-form templating "methodology" by:
# - Model: An array-of-objects (python: list-of-dictionaries) from a JSON or YAML file
#   - File (note: a single file) should have N-objects/dictionaries in an array
#   - Utility will detect (YAML, JSON) format from file suffix ( .json, *.yaml) and load it as "the model"
#   - Model parameter names (object/dictionary keys) may be anything except for the (few) "internal keys" (see below)
#   - Internal obj/dict keys:
#     - ofn - Ouput filename - a relative (or abs) pathname to output filename
#   - One model item (of N items) at the time is used to expand the template N times
# - Template - single template file containing Python Jinja 2 compatible templating notation
#   - This single template will be expanded N (number of parameter itmes) times to produce N files as output.
#   - Must comply to Jinja 2 notation
#   - The template vars must comply with model vars (vars here is synonym w. parameters)
# 
# ## Notes / Suggestions / Conventions
# 
# - Keep template filenames suffixed with Jinja 2 suffix ".j2", however so that also the final format is included in the name
#   thus e.g. templated yaml file might be called "server_confif.yaml.j2" for good documenatational value.
# - Keep model filename suffix to .json or .yaml for supported formats (respectively)
# - TODO: Cover notes on multi-doc YAML
# - Once more: check that the parameters (key-value pairs) in your model match the template varoiables used in Jinja 2 templates
#   - Extra variables in parameters do not hurt when expanding templates (they are just simply not used)
#   - Missing parameters in model may / will throw an exception when expanding a template.
#   - Note this applies to all objects / dictionaries in the model
# - Keep model (.yaml or .json) and template in the same git project as where
#   generated content is and preferably document how (and what) to run to
#   reproduce output (with changes in either model or template).
# - The documentation aspect applies especially if you are using
#   tmplgen.py utility from outside of codebase.
# - TODO: Consider using config file (when the support comes around)
# - Keep first part of the file basename of all template-project associated files to the same name to have
#   them easily recognizable as belonging together (e.g. my-proj.yaml, my-proj.txt.j2, my-proj.defaults.yaml)
# ## Running the utility
# ```
# bin/tmplgen.py gen --modelfn tdata/car.model.yaml --tmplfn tdata/car.json.j2 --joinfn engine:tdata/car.defaults.yaml --defaultsfn tdata/car.defaults.yaml --path /tmp/ --debug
# ```
# ## Roadmap
# - Allow merging default values (one global set of defaults) to model objects when parameter is missing
#   (config/cl-param: defaultsfn). This shortens and simplifies the model significantly.
# - Allow plugin/callback based processing of model (e.g. defaulting, validation) by loading a python file
# - Allow passing config file with: model, template, defaults, debug-level ...
import dputpy.dputil as dputil
import dputpy.merger as mrg
import os
import sys # sys.argv
import json
import yaml
import argparse
import time
import copy # copy.deepcopy()
import re
_parser = None

# Load YAML or JSON "model".
# *This* app expects the returned "handle" to be an array / list (of objects)
def load_json_or_yaml(fn):
  if not os.path.isfile(fn): raise "File '"+fn+"' does not exist"
  cont = open(fn, "r").read()
  if not cont: raise "No config content gotten from '"+fn+"'"
  cfg = None
  if fn.endswith(".json"): cfg = json.loads(cont)
  elif fn.endswith( (".yaml", ".yml")):
    cfg = yaml.safe_load(cont)
  # See if this is needed ?
  # y = yaml.load_all(data, Loader=Loader) # multidoc ????
  if not cfg: raise "No config data (dict) gotten from config file '"+fn+"'"
  return cfg

# Merge defaults to all objects of items.
def items_mergedefaults(items, defs):
  defkeys = defs.keys()
  for it in items: mrg.dict_merge_defs(it, defs, defkeys=defkeys) # Merge Single dict-item it
  return
    #for dk in defkeys:
    #  # Key does not exist at all (Cannot use it.get(dk))
    #  if not dk in it:
    #    # Note: value can be any type, must stringify
    #    print("Adding/merging missing k-v: "+dk+"="+str(defs[dk])+"", file=sys.stderr) # 
    #    it[dk] = defs[dk]
def items_mergearrays(items, defs, attr):
  # Check
  if not isinstance(items, list): print("No items in array"); return 1
  if not isinstance(defs, dict): print("No defs in dict"); return 2
  if not attr: print("No (array) attr (to merge) given"); return 3
  if not defs.get(attr): print("No attr in defs dict"); return 4
  arr2 = defs.get(attr);
  
  if not isinstance(items, list): print("No attr "+attr+" of type list in defs dict"); return 5
  if len(arr2) < 1: print("No array items in defs["+attr+"] - nothing to merge"); return 6
  for it in items:
    arr_it = it.get(attr)
    # uselen = len(arr_it) if len(arr2) > len(arr_it) else len(arr2) # Min of 2
    if not arr_it:
      # import copy # copy.deepcopy(data)
      #it[attr] = [] # Fill in empty in hopes of merge
      it[attr] = copy.deepcopy(arr2) # Deep copy defs (arr2)
      continue
    # Loop arr. Which is longer ? Drive by defaults (defs should not influence beyound
    # its len).
    i = 0
    arr_it_len = len(arr_it)
    for dob in arr2:
      if i >= arr_it_len: break
      if not it.get(attr)[i]: it[attr][i] = copy.deepcopy(dob)
      
  return 0

# Join data (dict or list) from a json/yaml file to all items (or single dict)
# parameter "items" passed may be list or dict (This is detected and correct path of action is taken)
def items_join(items, member, jifn): # ji=Join item filename
  ji = None
  if isinstance(jifn, dict) or isinstance(jifn, list): ji = jifn
  else: ji = load_json_or_yaml(jifn);
  if not ji: print("No json/yaml loaded from join file "+jifn+" !");
  if isinstance(items, list):
    for it in items:
      it[member] = copy.deepcopy(ji) # Make private copy !
  elif isinstance(items, dict): # Note: items is actually single dict
      items[member] = copy.deepcopy(ji) # Make private copy !
  return items
def usage(msg):
  if msg: print(msg)
  # Subcomm ?
  print("Try one of subcommands: ") # + ' '.join( ops.keys() ) )
  for k in ops.keys():
    print("- "+k+" - "+ops[k]["title"]);
  print("Available command line arguments:");
  _parser.print_help()
  exit(1);


# Generate files by templating
# bin/tmplgen.py
def gencontent(args):
  # if not args: usage("gencontent: Must have args !")
  tmplfn  = args.get("tmplfn", "")
  modelfn = args.get("modelfn", "")
  path    = args.get("path", "")
  debug   = args.get("debug", "")
  if not tmplfn: usage("gencontent: Must have (--tmplfn)")
  if not modelfn  or (not os.path.isfile(modelfn)): usage("Model filename (by --modfn) must be given and be a valid file!")
  items = load_json_or_yaml(args.get("modelfn")) # Load model items
  if not isinstance(items, list): usage("loading the model(file) did not produce an array !! Make sure model contains an array (at top level) ")
  # Validate ofn ?
  #### NEW: Join ??? (First !) #####
  if args.get("joinfn"):
    ja = args.get("joinfn").split(':') # Join args (,2 max ?)
    if not os.path.exists(ja[1]): print("File ("+ja[1]+") to join as member "+ja[0]+" does not seem to exist");
    else: items_join(items, ja[0], ja[1]);
  #### Merge Defaults ??? #######
  if args.get("defaults"):
     #items_mergedefaults(items, {"address": "8765 Madness street"}); # print(json.dumps(items, indent=2));
     items_mergedefaults(items, args.get("defaults")); # print(json.dumps(items, indent=2));
  #for it in items: ...
  #OLD:tmplstr = open(tmplfn, "r").read() # Revive ?
  # Use dputpy templating. Loop through items, produce
  retarr = dputil.tmpl_gen(items, tmplfn, path=path, debug=debug)
  # When returning data, items / retarr has a new potentially valuable member "useofn"
  rc = retarr if args.get("retdata") else 0
  return rc

# Perform simple tempating: 1 param (yaml), 1 template, 1 output
# bin/tmplgen.py gensimple --modelfn tdata/singlecar.model.yaml --tmplfn tdata/car.json.j2 --joinfn engine:tdata/car.defaults.yaml --defaultsfn tdata/car.defaults.yaml --path /tmp/ --outfn cars/chevy.json --debug
def gensimple(args):
  debug = args.get("debug")
  it = load_json_or_yaml(args.get("modelfn")) # Single model item
  if not it: usage("No dict/object model gotten");
  if not isinstance(it, dict): usage("Model not in dict/object format for simple templating");
  if args.get("joinfn"):
    ja = args.get("joinfn").split(':') # Join args (,2 max ?)
    if not os.path.exists(ja[1]): print("File ("+ja[1]+") to join as member "+ja[0]+" does not seem to exist");
    else: items_join(it, ja[0], ja[1]); # Could have done [it]
  #### Merge Defaults ??? #######
  if args.get("defaults"): mrg.dict_merge_defs(it, args.get("defaults")) # , defkeys=defkeys
  ##### OUTPUT ####
  # Pass single item as (wrapped) array, adding property "ofn" to indicate output fn
  ofn = args.get("outfn"); # Inject ofn, relative path
  if ofn: it["ofn"] = ofn
  if not it["ofn"]: usage("Simple (single) file generation requires output file (in model file (ofn) OR by CLI --outfn) !!!")
  if re.match(r'^/', it["ofn"]): print("Warning: output fn is set to absolute path (make sure this oddity is what you want)!");
  if debug: print("Complete simple model (w. ofn):\n"+json.dumps(it, indent=2), file=sys.stderr);
  path = args.get("path") # or ".";
  tmplfn = args.get("tmplfn", "")
  debug  = args.get("debug", "")
  retarr = dputil.tmpl_gen([it], tmplfn, path=path, debug=debug) # Pass single item in array (!!!)
  return

# Generate diff commands to compare:
# - Old output in "established eare (Combine "path" + "ofn")
# - New tentative/scratch output generated in a temporary/scratch path
# The scratch path will reside under temp (and will currently not be cleaned up)
def gendiff(args):
  # Patch "path" to scratch path, Call gencontent with that, diff to originals
  oldtmp = args.get("path")
  # Create subdir (time.time() returns floating point !!!)
  tempdn = "/tmp/"+str(os.getpid())+"_"+str(time.time())+"/"
  os.mkdir(tempdn, 0o755)
  args["path"] = tempdn
  args["retdata"] = True # 
  args["debug"] = True # 
  items = gencontent(args) # Call as sub-handler !
  for it in items: # OLD: data
    oldofn = oldtmp + "/" + it.get("ofn")
    print("# Diff old, new(temp/tentative)")
    print("diff "+oldofn+" "+it.get("useofn")+"")
  return 0

# TODO: Merge defaults (see gencontent() )! OR Let gencontent(args) return data, then dump !
def modeldump(args):
  # args validation is completely done in gencontent()
  #### OLD #####
  #items = load_json_or_yaml(args.get("modelfn")) # Load model items
  #if args.get("defaults"):
  #   #items_mergedefaults(items, {"address": "8765 Madness street"}); # print(json.dumps(items, indent=2));
  #   items_mergedefaults(items, args.get("defaults")); # print(json.dumps(items, indent=2));
  #### NEW, SIMPLE ####
  args["retdata"] = True
  items = gencontent(args)
  if not items: usage("Items not gotten from data content creator!");
  #### OUTPUT/ DUMP  ####
  fmt = args.get("format", "")
  if fmt == "json": print(json.dumps(items, indent=2))
  # https://pyyaml.org/wiki/PyYAMLDocumentation
  elif fmt == "yaml": print( yaml.dump(items, Dumper=yaml.Dumper))
  else: print("Format (yaml or json) not passed or format not supported: '"+fmt+"'");
  return 0

# Subcommands
ops = {
  "gen":       {"title": "Generate Content by model using templating", "cb": gencontent},
  "modeldump": {"title": "Dump Model in json or yaml (use same parameters as gen)",                 "cb": modeldump},
  "gendiff":   {"title": "Generate Content and diff it against existing files (curr. commands only)", "cb": gendiff},
  # Detect template files under this path ?
  #"": {},
  # Simple 1:1:1 templating
  "gensimple": {"title": "Generate Content by single dict/object, single template (single output, use --outfn to indicate output file)", "cb": gensimple},
}
# Example of running
# ```
# # You *may* have to set PYTHONPATH (Python library path)
# export PYTHONPATH=.
# dputpy/bin/tmplgen.py --modelfn items.yaml --tmplfn linvm.txt.j2 --path /tmp --debug
# ```
if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Template Expander / Content Generator')
  _parser = parser
  parser.add_argument('--modelfn',  default="", help='JSON/YAML model file (array-of-objects, i.e. list-of-dicts)')
  parser.add_argument('--tmplfn',  default="", help='Template filename (for template to be expanded with model parameters)')
  
  parser.add_argument('--defaultsfn',  default="", help='Filename for default values to merge onto objects of model.')
  
  # Note: Must be on area where user has dir/file write accress
  parser.add_argument('--path',  default="", help='Alternative top-directory (prefix) path to add relative output-filename (ofn) paths to.')
  # https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
  #   not avail in Python 3.6.9 (Ubuntu)
  parser.add_argument('--debug', default=False, action=argparse.BooleanOptionalAction, help='Trigger verbose output for the templating process')
  #DONOTUSE:parser.set_defaults(debug=False)
  parser.add_argument('--format',  default="", help='Output format (for subcommand modeldump, use: json or yaml)')
  parser.add_argument('--joinfn',  default="", help='Join a YAML file to model (YAML), with arg: $MEMNAME:$FILENAME')
  parser.add_argument('--outfn',  default="", help='Output file for subcommand gensimple (relative path that appends to path given by --path)')
  #parser.add_argument('--xx',  default="", help='')
  
  if len(sys.argv) < 2: usage("Subcommand missing - please pass subcommand as first arg (see choices below ...).")
  op = sys.argv.pop(1)
  if not op: usage("No subcommand given (as first arg)")
  if not ops.get(op): usage("No subcommand '"+op+"' available");
  
  args = vars(parser.parse_args())
  modfn  = args.get("modelfn", ""); # Model/parameters
  tmplfn = args.get("tmplfn", ""); # Template filename (Jinja 2 - *.j2)
  deffn  = args.get("defaultsfn", ""); # Defaults filename
  path   = args.get("path", ""); # Alternative / Prefix path to generate content to
  debug  = args.get("debug", ""); # Verbose output
  #joinfn  = args.get("joinfn", ""); # Note: joinfn has member:fn notation
  need_m_t = {"gen": True, "gendiff": True} # Need model and template
  # Validate !!!
  if need_m_t.get(op):
    if not modfn  or (not os.path.isfile(modfn)): usage("Model filename (by --modfn) must be given and be a valid file!")
    if not tmplfn or (not os.path.isfile(tmplfn)): usage("template filename (by --tmplfn) must be given and be a valid file!")
    #if 
  if deffn and ( not os.path.isfile(deffn)): usage("Defaults filename (by --defaultsfn) must be a valid file");
  if path and not os.path.exists(path): usage("Optional root-path by --path must be a directory!")
  #if joinfn and not os.path.exists(joinfn): usage("Optional join filename by --joinfn does not exist!") # NOT a PLAIN FN !
  # Load defaults if present (here or later)
  if deffn: # defaults fn present - load data here for all subcommands (to use)
    args["defaults"] = load_json_or_yaml(deffn)
    if not isinstance(args.get("defaults"), dict): usage("Defaults file must contain dict/object (no other types - such as list - allowed)")
  #if not path: path = os.getcwd()
  args["op"] = op # Add op !
  rc = ops[op]["cb"](args)
  exit(rc);


