# Subcommands as CLI Operations.
# Allows subcommands to be associated to handler callbacks and
# other command meta info.
# See argparse:
# - Pyhon man: https://docs.python.org/3/library/argparse.html
# - Argparse tutorial: https://docs.python.org/3/howto/argparse.html
# - Google: python argparse example

import sys
import argparse

# Must be done outside __name == "__main__"
#this_module = sys.modules['__main__']
#this_module = __import__(__name__) # Orig ex. current_module
#print(f"This module: {this_module}");
def getmodulehandle():
  print(f"Module name: {this_module.__name__}")
  #return this_module.__name__ # for sys.modules['__main__']
  #print(f"Module name: {this_module.__name__}")
  #return this_module.__name__ # for __import__(__name__)
  return "NONE"
# TODO: Allow also "rich" set of meta data
def new(_ops, **kwargs):
  clapp = {"ops": _ops}
  debug = kwargs.get("debug") # or 
  if debug: print(f"Reporting module name: {__name__}");
  if not _ops: usage("Must have ops !")
  #ops = _ops
  #if kwargs["autohelp"]: clapp["ops"]["help"] = ...
  # Store argparse instance created by main application
  if kwargs.get("clopts"): clapp["clopts"] = kwargs["clopts"]
  #print(ops)
  return clapp

def clparse(ca, **kwargs):
  #global ops
  ops = ca["ops"]
  # Note the original "strip script name and subcommand" triggered arg parsing problem (error: unrecognized arguments: ...).
  # Must retain python script name in sys.argv as argparse
  # starts parsing sys.argv[1:] (wants to strip script name itself). Alt: add dummy script name back e.g. 
  #sys.argv = sys.argv[1:]
  if len(sys.argv) < 2: usage(ca, "No subcommand/op given")
  op = sys.argv.pop(1); # x = x[1:]. NEW 0 => 1
  #sys.argv.insert(0, "dummy") # putting dummy script name back as sys.arg[0] works as well
  if not op: usage(ca, "No subcommand/op given"); 
  cmdok = False
  if isinstance(ops, dict) and ops.get(op): cmdok = True
  if isinstance(ops, list):
    opn = next( (opn for opn in ops if opn.get("id") == op), None )
    if opn: cmdok = True
  if not cmdok: usage(ca, f"No subcommand {op} available")
  # TODO: Consider CL parameters (argparse)
  opts = {}
  ap = ca.get("clopts") # argparse instance
  if ap:
    # Note also: pargs, rawargs = parser.parse_known_args() # https://stackoverflow.com/questions/17118999/python-argparse-unrecognized-arguments
    if kwargs.get("debug"): print(f"CL/Args (sys.argv) before parsing: ", sys.argv)
    args = ap.parse_args() # parser.parse_args()
    opts = vars(args)
    #ALSO: ca["opts"] = opts # ???
  #print(ops)
  ca["op"] = op
  return opts

def usage(ca, msg, **kwargs):
  #global ops
  ops = ca["ops"]
  if msg: print(msg)
  #print(ops);
  oplist = None
  if   isinstance(ops, dict): oplist = ops.keys()
  elif isinstance(ops, list): oplist = map(lambda x: x.get("id"), ops);
  print("Try one of the subcommands: "+", ".join(oplist))
  exit(0)
  #return

# Pass None (in app  __main__) to trigger parameterless call.
# One app can only have one form of call for all handlers
def run(ca, p):
  #global ops
  ops = ca["ops"]
  op  = ca["op"]
  rc = 0
  cb = None # ops[op]
  case = 0
  #if 
  # list - search for op
  if isinstance(ops, list):
    # opn = filter(lambda x: x.get("id", "") == op, ops)
    #TODO:
    opn = next( (opn for opn in ops if opn.get("id") == op), None )
    cb = opn.get("cb")
    case = 1
  # OoO / Python DoD
  elif isinstance(ops, dict):
    # OoF / DoF
    if callable(ops[op]): cb = ops[op]; case = 2
    elif isinstance(ops[op], dict): cb = ops[op].get("cb"); case = 3
  if not cb: print(f"No callback concluded for action (case: {case})!"); return
  if p:  rc = cb(p) # ops[op](p)
  else:  rc = cb()  # ops[op]()
  return rc

def is_all_func(d):
  nonfunc = 0
  for k in d.keys():
    if not type(d[k]) is func: nonfunc += 1
  return not nonfunc

# Self-test / cliapp usage example / cliapp dev utility
def gen_ap(opts):
  ans = opts.get("argnames") # Expect str
  ans = ans.split(",")
  appn = opts.get("appname") or "My Application"
  # TODO: add App name ??? opts.get("appname")
  print(f"  parser = argparse.ArgumentParser()"); # description="{appn}"
  print(f"  # Also nargs='?', action='...', const='' (overload between bool and valued arg)");
  for a in ans:
    print(f"  parser.add_argument(\"{a}\", type=str, default=\"\", help=\"\")")

def gen_subcomm(opts):
  scarr = [];
  scnames = opts.get("scnames")
  scnames = scnames.split(",")
  import json
  print("ops = [");
  for scn in scnames:
    e = {"id": f"{scn}", "title": f"Subcomm {scn}", "cb": None}
    print(f"  {json.dumps(e)},")
    #scarr.append(e)
  print("]");
  gen_ap(opts);
  #print(f"ops = {json.dumps(scarr, indent=2)}")
ops = [
  {"id": "argparse_opts", "label": "Generate argparse instantiation and argument registration calls (Pass --argnames ans optionally --appname)", "cb": gen_ap},
  {"id": "subcommands", "label": "Generate an array of subcommands (Pass --scnames)", "cb": gen_subcomm},
]

if __name__ == "__main__":
  #print("clapp dev utilities ...")
  # Google: python getting handle to module inside the module itself
  # Google: python getting handle to module inside the module itself while executing as __main__
  # Problem:  the __name__ is "__main__"
  #this_module = sys.modules[__name__]
  # Scores KeyError: 'dputpy.clapp' ... as module is loaded as __main__, not a module (does not go to system registered modules)
  #this_module = sys.modules["dputpy.clapp"]
  #this_module2 = getmodulehandle()
  #print(f"Module reports: {this_module2}");
  parser = argparse.ArgumentParser()
  # Can use "--" prefix on argname to denote optional. Seems "--" prefix and default="..." are mutually exclusive
  parser.add_argument("--argnames", type=str, default="opt1,opt2,opt3", help="Argument names to generate argparse instantiation from", required=False,)
  parser.add_argument("--appname", type=str, default="My App", help="Application (descriptive) name", required=False, )
  parser.add_argument("--scnames", type=str, default="sub1,sub2,sub3", help="Subcommand names as used on the CLI", required=False, )
  cla = new(ops, clopts=parser)
  opts = clparse(cla, debug=1)
  print("Opts gotten: ", opts);
  run(cla, opts)
