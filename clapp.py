# Subcommands as CLI Operations.
# Allows subcommands to be associated to handler callbacks and
# other command meta info.

import sys
import argparse

#ops = {}

# TODO: Allow also "rich" set of meta data
def new(_ops, **kwargs):
  #global ops
  clapp = {"ops": _ops}
  if not _ops: usage("Must have ops !")
  #ops = _ops
  #if kwargs["autohelp"]: clapp["ops"]["help"] = ...
  #print(ops)
  return clapp

def clparse(ca):
  #global ops
  ops = ca["ops"]
  sys.argv = sys.argv[1:]
  if not len(sys.argv): usage(ca, "No subcommand/op given")
  op = sys.argv.pop(0); # x = x[1:]
  if not op: usage("No submommand/op given")
  if not ops.get(op): usage(ca, "No subcommand "+op+" available")
  # TODO: Consider CL parameters (argparse)
  # ...
  
  #print(ops)
  ca["op"] = op
  return

def usage(ca, msg, **kwargs):
  #global ops
  ops = ca["ops"]
  if msg: print(msg)
  #print(ops);
  print("Try ops: "+", ".join(ops.keys()))
  exit(0)
  return

# Pass None (in app  __main__) to trigger parameterless call.
# One app can only have one form of call for all handlers
def run(ca, p):
  #global ops
  ops = ca["ops"]
  op  = ca["op"]
  rc = 0
  if p:  rc = ops[op](p)
  else:  rc = ops[op]()
  return rc

def is_all_func(d):
  nonfunc = 0
  for k in d.keys():
    if not type(d[k]) is func: nonfunc += 1
  return not nonfunc
