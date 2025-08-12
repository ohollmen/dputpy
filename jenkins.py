#!/usr/bin/env python3
import dputpy.httpreq as httpreq
import urllib.parse

cfg = {"host": "localhost"}
def jrun(url, **kwargs):
  p = kwargs.get("params")
  ps = ""
  if p: ps = paraser(p)
  url_f = f"https://{cfg.get('host')}/{url}" # *Full* URL
  if ps: url_f += f"?{ps}"
  print(f"Build '{url_f}'")
  # Call 
  hdrs = {} # "Accept": "application/json"
  #httpreq.request('get', url_f, debug=1, headers=None)
  cmd = httpreq.curlify('get', url_f, **kwargs)
  print(cmd);

# https://stackoverflow.com/questions/1695183/how-can-i-percent-encode-url-parameters-in-python
def paraser(p):
  kva = []
  for k in p.keys():
    #kva.append(f"{k}={str(p[k])}")
    # TypeError: quote_from_bytes() expected bytes
    kva.append(f"{k}={urllib.parse.quote(str(p[k]), safe='')}") # safe='/', encoding=None, errors=None
  return "&".join(kva)
    
# Parse params from delimeted k=v (pair) string w. pairs separated by sep.
def getparams(pstr, sep):
  if not sep: sep = "\n"
  #pstr = pstr.trim();
  p = {}; # "\n" VVV
  for l in pstr.split(sep): # .forEach( (l) => { let kv = l.split('='); 
    kv = l.split('=')
    p[kv[0]] = kv[1]
  #if (!Object.keys(p).length) { return null; }
  return p
if __name__ == "__main__":
  print("Run Jenkins job")
  tp = {"a": "1", "b": 2}
  jrun('job/foo')
  jrun('job/foo', params=tp)