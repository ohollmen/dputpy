#!/usr/bin/python3

import dputpy
import json
import os
import dputpy.dputil as dputil
import dputpy.gcputil as gcputil
import dputpy.indexer as indexer
import dputpy.filefmttest as ft
#print("Welcome to dputpy !");

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

# CSV
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
#test_yaml_parsing()
#run_run_testing()
#key_testing()
#test_yaml2csv()
#test_indexer()
#test_file_hash_num()
chage = ft.chage_parse(os.environ.get('USER'), debug=1)
print(json.dumps(chage, indent=2))
d = ft.chage_tdelta(chage, "pw_lastch");
print("Delta: "+str(d));
