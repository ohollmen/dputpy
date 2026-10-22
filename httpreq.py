#!/usr/bin/env python3
# Helper for calling REST APIs (from python requests)
import requests
import sys # sys.stderr
import json
import base64
# import time

bodymeth = ["post","put","patch"]
std_hdrs = {"Content-Type": "application/json",  "Accept": "application/json"} # "Authorization": "Bearer ",
# Helper for "API (endpoint) lookup table". Fill in params here ? Add method as (optional kwargs) param ? place params to kwargs ?
# Return API Entry Point
def api_lookup(atab, aid, params): # Register atab, do not pass here ?
  def matchaid(apiep): return apiep.aid == aid
  ep = filter(matchaid, atab)
  return ep # Entry point

# fill-in params in URL. Perform this before calling httpreq.request()
def url_templated(purl, p, **kwargs):
  # Recall python native / built-in templating (No dependencies !!!)
  if kwargs.get("pq") and isinstance(kwargs["pq"], dict): pass # dict.keys().map()
  furl = purl.format(**p)
  # print(f"Generated/Templated URL: {furl}");
  return furl

# Set Basic or Bearer token credentials in HTTP request headers
# - atype: Auth type "basic" or "bearer" or arbitrary http header key (e.g. "x-apikey")
# - aval:
#   - Basic username and password in format "username:password" (will be b64 encoded) or ...
#   - Bearer Token (as-is, will not be b64 encoded) or ...
#   - Header (as-is) Value for arbitrary HTTP header key give in atype
# Credentials are always set into Autorization header. If AUthorization header was set before it will be overwritten.
def creds_set(hdrs, atype, aval):
  if not isinstance(hdrs, dict): raise Exception('Local: No HTTP Headers passed for creds addition.');
  # Basic - b64 encode
  if atype.lower() == 'basic':
    bc_b = base64.b64encode( aval.encode("utf-8") ).decode("utf-8")
    #bc_s = base64.b64encode(bc_b).decode("utf-8") # str() conversion leaves "b'...'" into string
    #hdrs["Authorization"] = "Basic "+str(base64.b64encode( aval.encode("utf-8") ).decode("utf-8")  )
    hdrs["Authorization"] = f"Basic {bc_b}"
  # Bearer - keep as-is
  elif atype.lower() == 'bearer': hdrs["Authorization"] = f"Bearer {aval}"
  # Any Other (e.g. x-api-key), keep header key and auth. value as-is
  elif atype: hdrs[atype] = aval # Allow type to be arbitrary key (e.g. "x-apikey") and use as 
  return hdrs

def file_to_b64(fname):
  #import base64
  import os
  if not fname: return None
  if not os.path.exists(fname): return None
  cont = open(attpath, "r").read()
  if not isinstance(cont, bytes):
    cont = cont.encode("utf-8") # Should now be bytes for 
  # (OLD: cont.encode("utf-8"))
  cont = base64.b64encode(cont).decode("utf-8")
  return cont

# Compact JSON/REST Request Handling for all methods
# - meth - HTTP Method (get, post, put, ...)
# - url - Full URL to call
# - keyword args (in kwargs)
#   - data=... - Body data for PUT, POST
#   - headers=... - Dict with keys and values to use for request headers
#   - debug=True - Turn on debug output
# https://stackoverflow.com/questions/39324970/python-requests-dynamically-pass-http-verb
def request(meth, url, **kwargs):
  # Note: Must del to not cause TypeError: Session.request() got an unexpected keyword argument 'debug'
  debug = kwargs.get("debug")
  if debug: del kwargs['debug']
  rresp = 0
  if kwargs.get("rresp"): rresp = 1; del kwargs["rresp"]
  if not isinstance(kwargs, dict): raise Exception('Local: No HTTP request related params');
  kwargs["url"] = url
  #hdrs = copy.deepcopy(std_hdrs)
  #### if not kwargs.get("headers")
  hdrs = kwargs.get("headers")
  if not hdrs: hdrs = kwargs["headers"] = {}
  else: hdrs = kwargs["headers"]
  print("Initial headers: ", hdrs);
  # Is one of the HTTP Methods requiring Body (POST,PUT,PATCH)
  bmeth = meth.lower() in bodymeth # bodymeth.contains(meth)
  #needser = # Need serialization (dict, list)
  # Per C.G. requests should handle setting content-length internally.
  if   bmeth and isinstance(kwargs.get("data"), str): pass # hdrs['Content-Length'] = str( len( kwargs.get('data') ) )
  elif bmeth and not kwargs.get("data"): raise ValueError(f"Local: No body kw 'data' for body-based method '{meth}'")
  # New: Auto-detect "data handle" and ser. to string (how was this working before)
  elif bmeth and isinstance(kwargs.get("data"), dict) or isinstance(kwargs.get("data"), list):
    hdrs["Content-Type"] = "application/json"; kwargs["data"] = json.dumps(kwargs["data"])
  # Also: httphdlr = getattr(requests, meth, None); if not httphdlr: raise ValueError("No http method handler found")
  # Overlay STD
  if not hdrs.get("Accept"): hdrs["Accept"] = "application/json"
  # Allow existing/explicit Content-Type to prevail (take over)
  if bmeth and not hdrs.get("Content-Type"): hdrs["Content-Type"] = "application/json"
  #print("Call ("+meth+") " + url)
  if bmeth and debug:
    print(f"BODYMETH({meth}) HEADERS:", kwargs.get("headers"), file=sys.stderr);
    print(f"BODY: '{kwargs.get('data')}'", file=sys.stderr)
  try:
    # Need to copy ONLY ["url","hdrs","data"] to new kwargs ?
    resp = requests.request(meth, **kwargs)
    if debug or (resp.status_code != 200): print("Received status: "+str(resp.status_code));
    resp.raise_for_status()
    # Client may want to inspect / access the whole response
    if rresp: return resp
    # ... but for most use-cases the convenience of getting only data is enough ....
    # Test if content-type json is promised, parse it
    if '/json' in resp.headers.get("Content-Type", ""): # OLD: == 'application/json':
      print("Treat resp as JSON", file=sys.stderr);
      jdata = resp.json()
    else: jdata = resp.text
    return jdata # Complete JSON response data !
  except requests.exceptions.RequestException as e:
    # logger.error
    print(f"Error: {meth} request to {url} failed with error: {e}", file=sys.stderr)
    return {"error": str(e)}
  return {}
# Curlify request by request params to a curl command.
# Must pass meth(od): GET,POST,PUT,HEAD, ...
# Support kwargs:
# - "headers" - "Accept","Content-Type","Authorization"
# - "data" (body) - But only on body methods
# Return curl command string to test equivalent request in terminal ("curlification" does NOT execute it).
def curlify(meth, url, **kwargs):
  cmd = f"curl -X {meth.upper()} ";
  hdrs = kwargs.get("headers")
  body = kwargs.get("data") # Moved up from bmeth test
  def complexdata(body):
    return (isinstance(body, dict)) or (isinstance(body, list))
  # TODO/AUTO:
  if complexdata(body) and not hdrs["Content-Type"]:
    hdrs["Content-Type"] = 'application/json' # May override too much if set !
  bmeth = meth.lower() in bodymeth # bodymeth.contains(meth)
  for hk in ["Accept","Content-Type","Authorization"]:
    if hdrs and hdrs.get(hk): cmd += f"-H '{hk}: {hdrs[hk]}' "
  if bmeth and kwargs.get("data"):
    if (isinstance(body, dict)) or (isinstance(body, list)): body = json.dumps(body)
    # isinstance(body, str) and
    elif  not body: body = '' # For odd APIs like Jenkins (POST w. empty body)
    cmd += f"-d '{body}' "
  cmd += f"'{url}'"
  return cmd

# Paged JSON Fetcher
# # Typical: Use max page size that service supports (e.g. 100)
# mpf = httpreq.multipagefetcher(100, "per_page", "page")
class multipagefetcher():
  def __init__(self, pp=100, ppkey="per_page", pnkey="page", **kwargs):
    self.pp = pp
    self.ppkey = ppkey
    self.pnkey = pnkey
  # Get (GET) JSON data pages and aggregate to one LoD / AoO.
  # Paging params are always passed in GET params
  # Assume API returns an empty array when page (number) is off the limits
  def get_pages(self, url, headers, **kwargs):
    #pp = self.pp # or 100 # Per page
    pnum = 1 # Always 1-based ? Separate flag for 0-based page number ?
    #if self.initpn: pnum = self.initpn # Initial page number
    para = {}; para[self.ppkey] = self.pp; para[self.pnkey] = -1; # Paging params
    results = []
    sess = kwargs.get("sess") if kwargs.get("sess") else requests.Session(); sess.headers.update(headers) # Set additionally hdrs ?
    if kwargs.get("debug"):
      import time
      time1 = time.time() # Also: int(time.time() * 1000)
    while True:
      para[self.pnkey] = pnum
      if kwargs.get("debug"): print(f"Page: {pnum} ({len(results)} ents.)")
      resp = requests.get(url, headers=headers, params=para) # {'per_page': per_page, 'page': page}
      #resp = sess.get(url,  params=para) # {'per_page': pp, 'page': pnum} # headers=headers,
      resp.raise_for_status()
      data = resp.json()
      # res.extend() would misbehave on plain obj
      if isinstance(data, dict): results.append(data) # Single obj
      else: results.extend(data)  # always append ? covers the final partial page too
      if len(data) < self.pp: break
      pnum += 1
    if kwargs.get("debug"): print({"entcnt": len(results), "pnum": pnum, "pp": self.pp,  "pps": (pnum / (time.time() - time1) )}) #
    return results
# 
# Small CLI testbed.
if __name__ == "__main__":
  """
  resp = request('get', "https://dog.ceo/api/breeds/image/random"); # https://dog.ceo/dog-api/
  print(resp);
  # Note: This can be done by: url.format(**para)
  turl = url_templated("https://dog.ceo/api/breeds/image/{breed}", {"breed": "random"});
  resp = request('get', turl); # Actual breeds (e.g. malamute, spaniel-japanese) do not work (!?)
  print("RESP(1):", resp);
  """
  # https://reqbin.com/req/v0crmky0/rest-api-post-example
  p = {"Id": 78912,"Customer": "Jason Sweet","Quantity": 1,"Price": 18.00}
  # https://reqbin.com/echo/post/json <= N/A
  # Also: https://httpbin.org/post
  print("POST-TEST: ...")
  hdrs = {"Content-Type": "application/json", "Accept": "application/json"}
  # No need to Change data=... to json=... (request() detects the need to 
  resp = request("post", "https://postman-echo.com/post", data=p, headers=hdrs)
  print("RESP(2):", resp); # print(resp.json())
  
  #resp = request("post", "https://reqbin.com/echo/post/json", );
  #print(resp)
  import os
  token = os.environ.get("GH_TOKEN")
  if not token: print("No GH_TOKEN, cancel request !", file=sys.stderr)
  hdrs = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github.v3+json'}
  hdrs["X-GitHub-Api-Version"] = "2022-11-28" # "2022-11-28" / "2026-03-10"
  ghurl = f"https://api.github.com/orgs/raspberrypi/repos" # {os.environ.get('USER')} # google (2927), broadcom (186)
  mpf = multipagefetcher(100, "per_page", "page") # httpreq.
  print(curlify('GET', ghurl, headers=hdrs))
  ents = mpf.get_pages(ghurl, hdrs, debug=1) # api/v3/
  #print(json.dumps(ents, indent=2))
  print(f"Got {len(ents)} ents.");
