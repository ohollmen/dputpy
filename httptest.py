# Test App URL:s by http(s).
# Requires file with appinfo on top and
# Nodes with test entrypoint info + parameters
# URL:s do not need to be unique, but same URL may be tested with
# many http methods (e.g. get, post, head) and parameters
# Members:
# - url - full url or subpath (in wich case the servurl from app is prefixed). Empty string here means server top level w. trailing "/",
#     "/" between server and path is added automatically
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
import time
import dputpy.httpreq as hreq
import requests

okmeth = {"get": True, "post": True, "patch": True, }
appmock = {"name": "MyApp", "servurl": "https://myserv:1000", "headers": {"":""},
  "urls": [
    {"url": "path/to", "method":"get", "ctype": "", "params": {"": ""}, "paramfn": "", "authlbl":"", "headers": None, "expect": "pass"}
]}
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
  urls = app["urls"] = list(filter(lambda u: not u.get('disa'), urls))
  for u in urls:
    if not u.get("url"): u["url"] = ""
    if not u.get("method"): u["method"] = "get"
    u["method"] = u["method"].lower() # Force lowercase
    # URL can be empty for "root url"
    #if not url: raise ValueError("URL missing from test")
    # paramfn (for now) takes precedence (we don't even detect conflict)
    pfn = u.get("paramfn")
    if pfn and os.path.exists(pfn):
      cont = open(pfn, "r").read()
      if cont.startswith("{") or cont.startswith("["): j = json.loads(cont); u["params"] = j
      else: u["params"] = cont # String !!!
      
    if not "headers" in u or not isinstance(u.get("headers"), dict): u["headers"] = {}
def body_prep():
  return
# TODO: Allow various filtering options in **kwargs
# runall() ?
def runtests(app, **kwargs):
  urls = app.get("urls")
  apphdrs = app.get("headers")
  lastresp = None
  for u in urls:
    #if u.get("disa"): continue
    url = u.get("url")
    m = u.get("method")
    if not url.startswith("http"): # and not url.startswith("/"):
      url = f"{app.get('servurl')}/{u.get('url')}"
    # Credentials !!! By url.authlbl lookup from app.creds
    hdrs = {}
    uhdrs = u.get("headers") # Also merging by: d3 = d1 | d2 or d3 = {**d1, **d2}
    if apphdrs: hdrs.update(apphdrs) # App
    if uhdrs:   hdrs.update(uhdrs) # URL
    #hreq.creds_set(hdrs, 'basic', self.creds)
    kwp = {"url": url, "headers": hdrs}
    # TODO: Support for application/x-www-form-urlencoded (urlenc)
    if m in hreq.bodymeth and "params" in u: # Bodymeth ???
      print(f"Assigning params (params type: {type(u.get('params'))}");
      if isinstance(u.get("params"), str): kwp["data"] = u.get("params")
      elif isinstance(u.get("params"), dict): kwp["json"] = u.get("params")
    # NOTE: We deal w. request on sufficiently low level to warrant use of "requests"
    clen = str( len(u.get("params")) ) if isinstance(u.get("params"), str) else "N/A"
    print(f"Call '{url}' ({m}) w. params type: {type(u.get('params'))} len: {clen}");
    #resp = hreq.request(u.get("method"), url, **kwp)
    t1 = time.time()  # Time
    resp = requests.request(m, **kwp)
    u["resptime"] = td = time.time() - t1  # Time
    # Analyze against "expect" ("fail" / "pass")
    # TODO: t_analyze(u, resp): # Write to "result"
    # https://www.w3schools.com/python/ref_requests_response.asp
    u["respcode"] = rc = resp.status_code
    #resp.raise_for_status()
    ok = is_2XX(rc)
    expass = True if u.get("expect") == "pass" else False
    res = "FAIL"
    u["resplen"] = rclen = len(resp.text)
    if ok: print(f"Response Code {rc} (resp-len: {rclen}B, time: {td})")
    if ok and not expass: print("FAIL (expectation: fail)")
    elif not ok and expass: print("FAIL (expectation: pass)")
    else: res = "PASS"; print(f"PASS (expectation: {u.get('expect')})")
    # Write to "result"
    u["result"] = res # "testresult"
    print(f"Res-cont: {resp.text}")
    u["respcont"] = lastresp = resp.text # Cloud also parse based on ... headers or '{'
    #if resp.headers.get("content-type") == 'application/json':
    if u["respcont"].startswith("{"): u["respjson"] = resp.json()
    if resp.text.startswith("{") or resp.text.startswith("["): j = json.loads(resp.text); lastreps = j
    
def is_2XX(rc):
  if rc >= 200 or rc <300: return True
  return False

def summary(app):
  urls = app.get("urls")
  for u in urls:
    u['method_u'] = u['method'].upper()
    print("# URL: {url} ({method_u})".format(**u))
#    print(f"""- Result: {u.get('result')}\n- Time: {u.get('resptime')}
#- Response-Body-len: {u.get('resplen')}""");

def docs(app):
  urls = app.get("urls")
  for u in urls:
    u['method_u'] = u['method'].upper()
    if not u["url"]: u["url"] = "/"
    print("## {name} ({method_u} \"{url}\")\n".format(**u))
    print("\n{description}\n\nRequest Example:".format(**u))
    print(f"```\n{json.dumps(u.get('params'), indent=2)}\n```\nResponse Example:\n```\n{json.dumps(u.get('respjson'), indent=2) if u.get('respjson') else u.get('resptext')}\n```\n")
