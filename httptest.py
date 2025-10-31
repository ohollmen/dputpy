# Test App URL:s by http(s).
# Requires file with appinfo on top and
# Nodes with test entrypoint info + parameters
# URL:s do not need to be unique, but same URL may be tested with
# many http methods (e.g. get, post, head) and parameters
# Members:
# - url - full url or subpath (in wich case the servurl from app is prefixed)
# - method - HTTP request method to use (default: GET)
# - ctype - Use "urlenc" to serialize "params" to GET URL or POST body
#    as URL encoded (k1=v1&k2=v2)
# - params - Parameters data to serialize to JSON post
# - paramfn - Parameter filename to use to loadparams from (Detect
#    content as JSON if it starts with '{' or '[', otherwise expect
#    ctype "urlenc"
# - authlbl - Label for the type of auth to use
# - headers - special headers related to URL call
# - expect - Expectation on test: "fail" / "pass"
import json
import os
import dputpy.httpreq as hreq

okmeth = {"get": True, "post": True, "patch": True, }

# Convenience method to load test file (w. app info and app.urls)
def load(fn, **kwargs):
  try:
    jcont = open(fn, "r").read()
    j = json.loads(jcont)
    # if kwargs.get("validate"):
    # Validate
  except Exception as e:
    print(f"Failed to load file '{fn}' as JSON: {e}")
    return None
  return j

def urls_init(app):
  urls = app.get("urls")
  print(f"Initing app {app.get('name')} URL:s")
  if not isinstance(urls, list): raise ValueError("URL:s not in array")
  for u in urls:
    if not u.get("method"): u["method"] = "get"
    u["method"] = u["method"].lower() # Force lowercase
    if not url: raise ValueError("URL missing from test")
    # paramfn (for now) takes precedence (we don't even detect conflict)
    pfn = u.get("paramfn");
    if pfn and os.path.exists(pfn):
      jcont = open(pfn, "r").read()
      j = json.loads(jcont)
      u["params"] = j

# TODO: Allow various filtering options in **kwargs
# runall() ?
def runtest(app, **kwargs):
  urls = app.get("urls")
  for u in urls:
    url = u.get("url")
    if not url.startswith("http"): # and not url.startswith("/"):
      url = f"{app.get('servurl')}/{u.get('url')}"
    # Credentials !!! By url.authlbl lookup from app.creds
    hdrs = {}
    #hreq.creds_set(hdrs, 'basic', self.creds)
    resp = httpreq(u.get("method"), url, headers=hdrs)
    # Analyze against "expect" ("fail" / "pass")
    # TODO: t_analyze(u, resp): # Write to "result"
    rc = resp.status_code
    #resp.raise_for_status()
    ok = is_2XX(rc)
    expass = True if u.get("expect") == "pass" else False
    res = "FAIL"
    if ok: print(f"Response Code {rc}")
    if ok and not expass: print("FAIL (expectation: fail)")
    elif not ok and expass: print("FAIL (expectation: pass)")
    else: res = "PASS"; print(f"PASS (expectation: {u.get('expect')})")
    # Write to "result"
    u["result"] = res
    
def is_2XX(rc):
  if rc >= 200 or rc <300: return True
  return False
