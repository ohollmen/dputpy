#!/usr/bin/python3

import dputpy
import json
import os
import sys # sys.stderr
import dputpy.dputil as dputil
import dputpy.gcputil as gcputil
import dputpy.indexer as indexer
import dputpy.filefmttest as ft
import dputpy.setops as setops
import dputpy.clapp as clapp
import dputpy.bin.tmplgen as tmplgen

#print("Welcome to dputpy !");
import dputpy.merger as mrg

def test_yaml_parsing():
  #y = dputpy.dputil.yamlload("./tdata/dict.yaml");
  y = dputil.yamlload("./tdata/dict.yaml");
  print(json.dumps(y, indent=2));
  yarr = dputil.yamlload("./tdata/multidoc.yaml", Xmulti=1);
  print(json.dumps(yarr, indent=2));
def run_run_testing():
  res = dputil.run("ls -al /etc/passwd /etc/not_there");
  print(json.dumps(res, indent=2));
def key_testing():
  acct = {"saname":"myaccount", "projid":"myproject"}
  jwt = gcputil.key_get(acct, {});
  if not jwt: exit(1)
  print(json.dumps(jwt, indent=2));
  jwtfn = "/tmp/gcpServiceAccountKey.json"
  dputil.jsonwrite(jwt, jwtfn);
  print("Wrote: "+jwtfn);
  jwt = dputil.jsonload(jwtfn);
  if jwt: print("Was able to load JSON back !")

# Write CSV
def test_yaml2csv():
  yarr = dputil.yamlload("./tdata/multidoc.yaml", Xmulti=1);
  fn_csv = "/tmp/multidoc.csv"
  err = dputil.csv_write(yarr, fn_csv, sep='\t')
  if err: print("Error "+err+" writing CSV"); exit(1)
  print("Wrote: "+fn_csv);
def test_indexer():
  idx = indexer.index(yarr, "ssn")
  print(json.dumps(idx, indent=2));
  yarr[1]["ssn"] = "001" # Set non-unique
  idx = indexer.index(yarr, "ssn")
  # Detect non-uniq
  nucnt = indexer.nonunique(yarr, "ssn")
  print(str(nucnt)+" Non-unique item(s)");
def test_file_hash_num():
  n_0 = ft.file_as_number("tdata/zero")
  print("zero is "+str(type(n_0)));
  n_1 = ft.file_as_number("tdata/one")
  print("one is "+str(type(n_1)));
def test_chage():
  chage = ft.chage_parse(os.environ.get('USER'), debug=1)
  print(json.dumps(chage, indent=2))
  d = ft.chage_tdelta(chage, "pw_lastch");
  print("Delta: "+str(d));
def test_setops():
  d = setops.diff([1,2,3], [3,4,5])
  d = setops.diff([1,2,3], [4,5,6])
  d = setops.diff([1,2,3], [1,2,3])
  d = setops.diff([1,2,3], [1,2,3,4,5])
  print("Diff: "+json.dumps(d))
  u = setops.union([1,2,3], [3,4,5])
  u = setops.union([1,2,3], [1000,1001,1002])
  u = setops.union([1,2,3], [1,2,3])
  u = setops.union([1,2,3], [2])
  print("Union: "+json.dumps(u))
  i = setops.intersect([1,2,3], [3,4,5])
  i = setops.intersect([1,2,3], [4,5,6])
  i = setops.intersect([2,3,4], [1,2,3,4,5,6])
  print("Intersect: "+json.dumps(i))
  arr = [{"val": 1}, {"val": 2}, {"val": 3},]
  arr2 = [{"val": 1}, {"val": 2}, {"val": 3},{"val": 2}, {"val": 3},]
  idx = setops.indexby(arr, "val")
  print("Index: "+json.dumps(idx))
  vec = setops.vec(arr, "val")
  vec = setops.vec(arr2, "val")
  print("Vector: "+json.dumps(vec))
  vec = setops.vec(arr2, "val", unique = 1)
  print("Vector: "+json.dumps(vec))

def test_runparse():
  ret = dputil.run("cat /tmp/key.json", fmt='json')
  print(json.dumps(ret["data"], indent=2))
  if ret["data"].get("crv", "") == "P-256": print("Got crv = "+ ret["data"].get("crv", ""))

def test_merge():
  myd = {"a":1}
  defs = {"b":2}
  mrg.both_show(myd, defs)
  out = mrg.dict_merge_defs(myd, defs)
  print(out)
  arr1 = [None, {"c":3}, None, None]
  arr2 = [{}, {"d": 4}, {}]
  mrg.both_show(arr1, arr2)
  mrg.arrays_merge(arr1, arr2)
  print(arr1)
  arr1 = ["", "Yes"]
  arr2 = ["No", ""]
  mrg.both_show(arr1, arr2)
  mrg.arrays_merge(arr1, arr2)
  print(arr1)

def test_tmplgen():
  # Base items
  items = tmplgen.load_json_or_yaml("tdata/car.model.yaml");
  # Defaults to merge
  defs = tmplgen.load_json_or_yaml("tdata/car.defaults.yaml");
  # Use the defaults file to *also* join. Either filename or already loaded dict should work
  #tmplgen.items_join(items, "engine", "tdata/car.defaults.yaml")
  tmplgen.items_join(items, "engine", defs); # Raw Obj/dict
  tmplgen.items_join(items, "firingorder", [6, 1, 3, 4, 2, 5]); # Array/List
  tmplgen.items_mergedefaults(items, defs) # Also merge to top-level
  print(json.dumps(items, indent=2));
  retarr = dputil.tmpl_gen(items, "tdata/car.json.j2", path="/tmp/cars-output/", debug=1)
  return

# grep ^def selftest.py
# perl -p -e 's/^def\s+(w+)/$1/; print $_
ops = {
  "keytest": key_testing,
  "setops": test_setops,
  "runparse": test_runparse,
  "merge": test_merge,
  "tmplgen": test_tmplgen,
}



if __name__ == "__main__":
  #test_yaml_parsing()
  #run_run_testing()
  #key_testing()
  #test_yaml2csv()
  #test_indexer()
  #test_file_hash_num()
  #test_chage()
  #test_setops()
  cla = clapp.new(ops)
  clapp.clparse(cla)
  rc = clapp.run(cla, None)
  exit(0)
