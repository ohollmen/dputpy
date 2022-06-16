# Various file tests
# TODO: Add presense check (stat())
import os
import re
import json
import yaml
import configparser

def isjson(fn):
  f = open(fn, "rb")
  j = json.load(f)
  if data: return j
  return 0
# https://stackoverflow.com/questions/3220670/read-all-the-contents-in-ini-file-into-dictionary-with-python
def isini(fn):
  config = configparser.ConfigParser()
  hdl = config.read(fn)
  print(hdl);
  if hdl: return config
  return 0
def isyaml(fn):
  f = open(fn, "rb")
  y = yaml.safe_load(f)
  if y: return y
  return 0
fmts = {
  "json": isjson,
  "yaml": isyaml,
  "ini": isini,
};
# Test a short (e.g. single line) fir for equal content (exact match).
# 
def trimmed_equals(fname, contstr):
  if not os.path.exists(fname): return 0
  cont = open(fname).read().strip();
  if cont == contstr: return 1
  return 0


def contains_substr(fname, contstr, **kwargs):
  # Check presence
  cont = open(fname).read()
  if kwargs.get("isre"):
    print("Checking for (re) "+contstr);
    # TODO: Options in ...
    reopts =  re.MULTILINE # re.IGNORECASE |
    if kwargs.get("reopts"): reopts = kwargs.get("reopts")
    print("Have re opts: "+ str(reopts));
    p = re.compile(contstr, reopts)
    m = p.search(cont)
    #print(m)
    if m: return 1
    return 0
  # Literal
  if contstr.find(contstr) != -1:
    return 1
  return 0

# TODO: Does this search whole file
def contains_repatt(fname, restr, **kwargs):
  cont = open(fname).read()
  # p = re.compile(restr, re.IGNORECASE | re.MULTILINE)
  # m = p.search(cont)
  m = re.search(restr, cont)
  if m: return 1
  return 0

def has_format(fname, fmtid, **kwargs):
  cont = open(fname).read()
  if fmts.get(fmtid):
    print("Testing "+fname+" to be "+fmtid);
    print("By ... "+ str(fmts.get(fmtid)) );
    hdl = fmts.get(fmtid)(fname)
    print(hdl);
    #print( vars(hdl)["_dict"] ); # For ini the handle is non-data
    # <class 'collections.OrderedDict'>
    if hdl: return hdl
    return 0
  print("Not any of the supported formats")
  return 0

# Parse file as number.
# TODO: support float ?
def file_as_number(fname):
  # 
  cont = open(fname).read()
  # test first by 
  numre = r"\s*(\d+)\s*"
  m = re.search(numre, cont)
  if not m: print("Number could not be matched in "+fname); return None
  return int(m[1])
