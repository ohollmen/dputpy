#!/usr/bin/python

import dputpy
import json
import dputpy.dputil as dputil
import dputpy.gcputil as gcputil
print("Welcome to dputpy !");
#y = dputpy.dputil.yamlload("./tdata/dict.yaml");
y = dputil.yamlload("./tdata/dict.yaml");
print(json.dumps(y, indent=2));
y = dputil.yamlload("./tdata/multidoc.yaml", Xmulti=1);
print(json.dumps(y, indent=2));

res = dputil.run("ls -al /etc/passwd /etc/not_there");
print(json.dumps(res, indent=2));
acct = {"saname":"myaccount", "projid":"myproject"}
jwt = gcputil.key_get(acct, {});
if not jwt: exit(1)
print(json.dumps(jwt, indent=2));

jwtfn = "/tmp/gcpServiceAccountKey.json"
dputil.jsonwrite(jwt, jwtfn);
print("Wrote: "+jwtfn);
jwt = dputil.jsonload(jwtfn);
if jwt: print("Was able to load JSON back !")
