# Data Processing utilities (read and parse files, setup templating,
# execute facilitating system commands ...)
# (c) Olli Hollmen
# License: MIT
import json
import sys
import os
import jinja2
import re
import subprocess
import yaml # pyyaml
import csv

from yaml import CLoader as Loader, CDumper as Dumper
#from yaml import CLoader as SafeLoader, CDumper as Dumper

ver = "0.92"

def jsonload(fn):
  if re.search(r"\n", fn) or re.search(r"\[", fn) or re.search(r"\{", fn): data = fn
  else:
    fh = open(fn, 'r')
    data = fh.read()
  obj = json.loads(data)
  return obj

def jsonwrite(ref, fn):
  # Check type dict
  if not isinstance(fn, str): apperror("Filename not passed as string")
  if (not isinstance(ref, list)) and (not isinstance(ref, dict)): apperror("Data not passed as dict or list ref") # isinstance(ref,tuple) ?
  # TODO: try ...
  fh = open(fn, 'w')
  if not fh: apperror("Error opening "+fn+" for writing");
  fh.write( json.dumps(ref, indent=2)+"\n" )
  fh.close()
  return

def yamlload(fn, **kwargs):
  if   re.search(r"\n", fn): data = fn
  elif re.search(r"^---", fn): data = fn
  else:
    fh = open(fn, 'r')
    if not fh: return None
    data = fh.read()
  if kwargs.get("multi") or re.search(r'---', data): # 
    #y = yaml.load_all(data, Loader=yaml.SafeLoader) #
    y = yaml.load_all(data, Loader=Loader) #
    y = list(y)
  else:
    y = yaml.safe_load(data) # , Loader=yaml.SafeLoader
  return y
def yamlwrite(ref, fn):
  fh = open(fn, 'w')
  # TODO: Check multi-doc aspect
  fh.write( yaml.dump(ref, Dumper=yaml.Dumper) )
  fh.close()
  return

# dputil.tmpl_load(fn)
# Load template file and instantiate jinja2 template from it.
# Template is ready to use (Call ... on it)
# ```
# cust = { name: "John Smith", "amount": 80.00 }
# tmpl = dputil.tmpl_load("./tmpl/billing.j2")
# out = tmpl.render(**cust)
# ...
# ```
def tmpl_load(fn):
  tstr = open(fn, "r").read();
  template = jinja2.Template(tstr)
  return template

def fileload(fn):
  fh = open(fn, 'r')
  # TODO: stderr ...
  if not fh: return "";
  data = fh.read()
  if not data: return ""
  return data

def filewrite(cont, fn):
  fh = open(fn, 'w')
  fh.write(cont)
  fh.close()
  return

# dputil.run(cmd, onerror=errcb)
# TODO: Create higher level wrapping object for CL execution
# 
# (cmd, ret code, results in stdout, stderr).
# Both stdout and stderr are stored in returned dict.
def run(cmd, **kwargs):
  ret = {"rc": -10000, "out": None, "err": None}
  if isinstance(cmd, list): cmdarr = cmd
  else: cmdarr = cmd_arr(cmd)
  # Be slightly wasteful and store BOTH stdout and stderr for later
  # inspection (by caller). Seems text=... param not supported by older
  # version
  call = subprocess.run(cmdarr,
    stdout=subprocess.PIPE, stderr=subprocess.PIPE,  ) # text=True,
  ret["rc"]  = call.returncode
  # Note: Newer Python could just use test=True above
  ret["out"] = str(call.stdout.decode('utf-8')) # 'ascii'
  ret["err"] = str(call.stderr.decode('utf-8'))
  if ret["rc"] and kwargs.get("onerror"):
    # Check 
    kwargs.get("onerror")("run: Error From command: "+cmd)
  return ret

# dputil.cmd_arr(cmdstr)
# Chunk a simple string version command to be split to POSIX exec() style
# array of CL arguments to be used with python (exec-style) subprocess.run().
# Note: Implementation is naive and assumes every CL option NOT contain
# whitespace chars
def cmd_arr(cmdline):
  return re.split(r'\s+', cmdline);

def apperror(msg):
  print(msg);

# Write array of dictionaries into a CSV file
# Return errors
def csv_write(arr, fn, **kwargs):
  cfg = {}
  if not isinstance(arr, list): return 1
  fh = open(fn, "w")
  fldnames = kwargs.get("fldnames")
  
  # Sample (all fields) from first
  if not fldnames:
    fldnames = arr[0].keys()
  
  qc = kwargs.get("qchar")
  if not qc: qc = '"'
  sep = kwargs.get("sep")
  if not sep: sep = ','
  #cw = csv.writer(fh, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
  writer = csv.DictWriter(fh, fieldnames=fldnames, delimiter=sep, quotechar=qc, extrasaction='ignore')
  writer.writeheader()
  for e in arr: writer.writerow(e)
  fh.close()
  return 0

# Read CSV into LoD / AoO
def csv_load(fn, **kwargs):
  fldnames = kwargs.get("fldnames", None)
  sep = kwargs.get("sep", ',')
  fh = open(fn, "r")
  # restkey=None, restval=None,  dialect='excel',
  reader = csv.DictReader(fh, fieldnames=fldnames,  delimiter=sep)
  arr = [];
  for row in reader:
    arr.append(row)
  # Eliminate forst row, e.g. for a case where fldnames are passed explicitly,
  # but first row containes (unwanted) headers (e.g. spaces, in names, missing
  # column names).
  if kwargs.get("skipfirst"):
    arr.pop(0)
  return arr
