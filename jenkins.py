#!/usr/bin/env python3
import dputpy.httpreq as httpreq
import urllib.parse
import sys
import os # .environ
import time # time.time()
cfg = {"host": "localhost"}
# Take: params, 
def jrun(url, **kwargs):
  p = kwargs.get("params")
  ps = ""
  if p: ps = paraser(p)
  url_f = f"https://{cfg.get('host')}/{url}" # *Full* URL
  if ps:
    url_f += "buildWithParameters"
    url_f += f"?{ps}"
  else: url_f += "build"
  url_f +="?delay=0sec"
  #print(f"Build '{url_f}'")
  # Call
  hdrs = kwargs.get("headers")
  if not hdrs: hdrs = {}
  if kwargs.get("dryrun"):
    cmd = httpreq.curlify('post', url_f, **kwargs)
    #if kwargs.get("debug"):
    print(cmd);
  resp = httpreq.request('post', url_f, debug=1, headers=hdrs, data=ps, rresp=1)
  # Will progress: "queued" -> "building"-> "completed"
  # Appending "api/json" to progress location URL gives JSON progress response URL.
  progloc = resp.headers.get("Location") # Has (e.g.) https://JSERVER/queue/item/115900/
  binfo = {"ploc": progloc, "ploc_j": progloc + "api/json", "tout": 120, "polls": 3}
  return binfo

# Query progress based on initial build request response.
# Having "executable" (w. number,url) means build has started (.. is in quiet).
# Related URL:s
# - https://JSERVER/job/your-job-name/6789/consoleText
# - https://JSERVER/job/your-job-name/6789/logText/progressiveText?start=0
def prog_query(binfo, hdrs): # (iresp):
  #progloc = iresp.headers.get("Location")
  #progloc += "api/json"
  j = httpreq.request("get", binfo.get("ploc_j")) # "Accept": ...
  if not j: raise ValueError("No JSON response from progress query.")
  tilltime = time.time() + binfo.get("tout")
  
  while time.time() < tilltime:
    resp = requests.get(binfo.get("ploc_j"), headers=hdrs);
    if resp.status_code == 200:  
      if j and j.get("executable"):
        bi = j.get("executable")
        # On resp of this url "building" needs to transition from true => false (== done)
        # With "building": false, "result" will give SUCCESS, FAILURE or ABORTED.
        bproc = bi.get("url") # contains the id by "number"
        
      elif j.get("cancelled"):
        raise Exception("Build got cancelled !");
    elif resp.status_code == 404:
      # raise Exception("Queue item no more avail (Jenkins cleaned the job) !")
      print("Queue item no more avail (Jenkins cleaned the job) !")
      break
    time.sleep(binfo.get("polls"))
  raise TimeoutError("Build polling timed out !!!")
  #return
# https://stackoverflow.com/questions/1695183/how-can-i-percent-encode-url-parameters-in-python
def paraser(p):
  kva = []
  for k in p.keys():
    #kva.append(f"{k}={str(p[k])}")
    # TypeError: quote_from_bytes() expected bytes => must 
    kva.append(f"{k}={urllib.parse.quote(str(p[k]), safe='')}") # safe='/', encoding=None, errors=None
  return "&".join(kva)
    
# Parse params from delimeted k=v (pair) string w. pairs separated by sep.
# E.g. to parse kv pairs laid out on lines, pass sep = "\n"
# If whitespace is expected on pstr, perform pstr.strip() (or .lstrip(), .rstrip()) on caller side.
def getparams(pstr, sep):
  if not sep: sep = "&" # "\n"
  #pstr = pstr.strip();
  p = {}; # "\n" VVV
  for l in pstr.split(sep): # .forEach( (l) => { let kv = l.split('='); 
    kv = l.split('=')
    p[kv[0]] = kv[1]
  #if (!Object.keys(p).length) { return null; }
  return p
def usage(msg):
  print(msg);exit(1)

if __name__ == "__main__":
  
  if len(sys.argv) < 2: usage("No URL. Pass URL as first CL arg !")
  url = sys.argv[1]
  jhost = os.environ.get("JENKINS_HOST")
  if not jhost: usage("No JENKINS_HOST in env !")
  cfg["host"] = jhost
  print(f"Run Jenkins job: https://{jhost}{url}")
  jcreds = os.environ.get("JENKINS_CREDS")
  if not jcreds: usage("No JENKINS_CREDS given in env !")
  hdrs = {"Accept": "*/*"} # "Accept": "application/json"
  # Jenkins Creds (for account/user) are created by Right-top user icon => Security => API Token
  httpreq.creds_set(hdrs, 'basic', jcreds)
  print("main headers: ", hdrs);
  tp = {"a": "1", "b": 2}
  #jrun('job/foo/', dryrun=1, headers=hdrs)
  #jrun('job/foo/', params=tp, dryrun=1,  headers=hdrs)
  binfo = jrun(url, dryrun=0, headers=hdrs, params=None, debug=1)
  print("Track progress based on: ", binfo)
  hdrs2 = {"Accept":"application/json"}
  httpreq.creds_set(hdrs2, 'basic', jcreds)
  print("main headers (prog): ", hdrs);
  # prog_query(binfo, hdrs2)
