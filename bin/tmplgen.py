#!env python3
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
# 
# ## Roadmap
# - Allow merging default values (one global set of defaults) to model objects when parameter is missing
# - Allow plugin/callback based processing of model (e.g. defaulting, validation) by loading a python file
# - Allow passing config file with: model, template, defaults, debug-level ...
import dputpy.dputil as dputil
import os
import json
import yaml
import argparse

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

def mergedefaults(items, defs):
  defkeys = defs.keys()
  for it in items:
    

def usage(msg):
  if msg: print(msg)
  # Subcomm ?
  exit(1);
ops = {
  "gen": {},
  "json2yaml": {},
  "": {},
}
# Example of running
# ```
# # You *may* have to set PYTHONPATH (Python library path)
# export PYTHONPATH=.
# dputpy/bin/tmplgen.py --modelfn items.yaml --tmplfn linvm.txt.j2 --path /tmp --debug
# ```
if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Template Expander / Content Generator')
  parser.add_argument('--modelfn',  default="", help='JSON/YAML model file (array-of-objects)')
  parser.add_argument('--tmplfn',  default="", help='Template filename (fro template to be expanded with model parameters)')
  parser.add_argument('--path',  default="", help='Alternative top-directory path to add relative output-filename (ofn) paths to.')
  # https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
  parser.add_argument('--debug', default=False,  action=argparse.BooleanOptionalAction, help='Debug the templating process')
  #parser.set_defaults(debug=False)
  #parser.add_argument('--format',  default="", help='Output format (for dumping), json or yaml')
  #parser.add_argument('--xx',  default="", help='')
  #parser.add_argument('--xx',  default="", help='')
  args = vars(parser.parse_args())
  modfn  = args.get("modelfn", ""); # Model/parameters
  tmplfn = args.get("tmplfn", ""); # Template filename
  path   = args.get("path", ""); # Template filename
  debug  = args.get("debug", ""); # Template filename
  # Validate !!!
  if not modfn  or (not os.path.isfile(modfn)): usage("Model filename (by --modfn) must be given and be a valid file!")
  if not tmplfn or (not os.path.isfile(tmplfn)): usage("template filename (by --tmplfn) must be given and be a valid file!")
  if path and not os.path.exists(path): usage("Optional root-path by --path must be a directory!")
  #if not path: path = os.getcwd()
  #OLD:modstr = open(modfn, "r").read(); items  = json.loads(modstr) # Revive ?
  items = load_json_or_yaml(modfn) # Load model items
  if not isinstance(items, list): usage("loading the model(file) did not produce an array !! Make sure model contains an array (at top level) ")
  # Validate ofn ?
  #for it in items: ...
  #OLD:tmplstr = open(tmplfn, "r").read() # Revive ?
  # Use dputpy templating. Loop through items, produce
  dputil.tmpl_gen(items, tmplfn, path=path, debug=debug)
  exit(0)
