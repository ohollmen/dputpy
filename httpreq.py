# Helper for calling REST APIs (from python requests)
import requests
import sys # sys.stderr
import json
import base64

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
  # Per C.G. requests should handle setting content-length internally.
  if   bmeth and isinstance(kwargs.get("data"), str): pass # hdrs['Content-Length'] = str( len( kwargs.get('data') ) )
  elif bmeth and not kwargs.get("data"): raise ValueError(f"Local: No body kw 'data' for body-based method '{meth}'")
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
      jdata = resp.json()
    else: jdata = resp.text
    return jdata # Complete JSON response data !
  except requests.exceptions.RequestException as e:
    # logger.error
    print(f"Error: {meth} request to {url} failed with error: {e}", file=sys.stderr)
    return {"error": str(e)}
  return {}
# Curlify request by request params to a curl command.
# Return curl command string to test equivalent request in terminal ("curlification" does NOT execute it).
def curlify(meth, url, **kwargs):
  cmd = f"curl -X {meth.upper()} ";
  hdrs = kwargs.get("headers")
  bmeth = meth.lower() in bodymeth # bodymeth.contains(meth)
  for hk in ["Accept","Content-Type","Authorization"]:
    if hdrs and hdrs.get(hk): cmd += f"-H '{hk}: {hdrs[hk]}' "
  if bmeth and kwargs.get("data"):
    body = kwargs.get("data")
    if (isinstance(body, dict)) or (isinstance(body, list)): body = json.dumps(body)
    # isinstance(body, str) and
    elif  not body: body = ''
    cmd += f"-d '{body}' "
  cmd += f"'{url}'"
  return cmd

# Small CLI testbed.
if __name__ == "__main__":
  resp = request('get', "https://dog.ceo/api/breeds/image/random"); # https://dog.ceo/dog-api/
  print(resp);
  turl = url_templated("https://dog.ceo/api/breeds/image/{breed}", {"breed": "random"});
  resp = request('get', turl); # Actual breeds (e.g. malamute, spaniel-japanese) do not work (!?)
  print("RESP(1):", resp);
  # https://reqbin.com/req/v0crmky0/rest-api-post-example
  p = {"Id": 78912,"Customer": "Jason Sweet","Quantity": 1,"Price": 18.00}
  resp = request("post", "https://reqbin.com/echo/post/json", data=p);
  print("RESP(2):", resp)
  #resp = request("post", "https://reqbin.com/echo/post/json", );
  #print(resp)
