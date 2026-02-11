# # JSON-RPC Server side request handling
# ## JSON-RPC handler functions
# Expected signature: (params, kwargs)
# 
# # Notes
# Consider: mymod = importlib.import_module('to.mymodule'), also sys.path.insert(0, os.path.dirname(module_path)), self.functions[f"{module_name}.{name}"] = attr
# Also inspect, inspect.ismodule(mymod), inspect.signature(func)
import os
#import logging
import json

apis = {
  #"myns.mymeth": cb,
}
reqinit = {}
#cfg = {"passmethod": False} # passmethod - Pass method name in kwargs
# Note: This api addition does not consider URL (like in traditional REST)
def api_add(rpcmethod, handler, **kwargs):
  apis[rpcmethod] = handler
  # ricb signature: ()
  ricb = kwargs.get("reqinit")
  if ricb and callable(ricb): reqinit[rpcmethod] = ricb # Must be callable()
  return

# Detect/classify request as JSON-RPC request (slimmed down or full)
def req_is_rpc(datajson, **kwargs):
    print("Got RPC message to detect: ", datajson);
    if not isinstance(datajson, dict): return False
    # Method is important and will be used for dispatching. It should (prefearbly) be "namespaced", e.g. "jenkins.runjob"
    if not datajson.get("method"): return False
    # Allow even empty object (TODO: list ? None (if "params" not in datajson) ?)
    if not isinstance(datajson.get("params"), dict): return False
    # Per spec, this can be left out, but we require it until there is a reason to leave it out. All initial API:s require params.
    #if not datajson.get("params"): return False
    # Maybe later require FULL JSON-RPC formality/compatibility
    if kwargs.get("full"):
      if not datajson.get("id"): return False # "id" of req, same id will appear in response.
      if not datajson.get("jsonrpc"): return False # and ... != "2.0"
    return True # Looks like RPC

# Create complete RPC error response (NO result)
def rpc_error(msg, code=0):
  ec = -32000 if not code else code
  return { "error": {"code": ec, "message": msg} }

# Dispatch incoming JSON-RPC message to a correct method handler.
# This has to be called imperatively from a (e.g.) flash URL handler.
def dispatch(datajson):
  # try: # Catch anything bad happening in downstream callpath, rethrow as needed
  m = datajson.get("method")
  p = datajson.get("params")
  if not m: return rpc_error("No method in RPC request")
  # TODO: Consider array/list (?) or not isinstance(p, list)
  if not isinstance(p, dict): return rpc_error("Params not passed as Object (dict)")
  # Lookup method
  if not apis: return rpc_error("No methods available in service!") # In python also empty counts as falsy
  cb = apis.get(m)
  if not cb: return rpc_error(f"Error in RPC dispatchg: Unknown method '{m}'")
  if not callable(cb): return rpc_error(f"Error registered  method '{m}' is not callable")
  # Have a module defined cb for figuring out kwargs ? Always pass rpc as a helper 
  # cbkwa = {"rpc": 1} # Add module desired args to this.
  ricb = reqinit.get(m) # Request init cb to call just before method.
  # Raise even in request preparation step (if given)
  try:
    if ricb: ricb(p)
  except Exception as e:
    return rpc_error(f"Exception during request preparation for method {m}")
  try:
    retval = cb(p, debug=True,rpc=True,method=m)
  except Exception as e:
    return rpc_error(f"Exception during request handling of method {m}")
  if not retval: return rpc_error("RPC Dispatching produced None internally !")
  if not isinstance(retval, dict):  return rpc_error("RPC Dispatching produced non-object (non-dict) !")
  # logging.debug(f"Survived Result type-checks (Is {type(retval)}) !")
  if retval.get("error"): finres = retval
  else: finres = {"result": retval, }
  # Check if "full" JSON-RPC request was sent, reflect it's "id","jsonrpc"
  if datajson.get("id"): finres["id"] = datajson.get("id")
  if datajson.get("jsonrpc"): finres["jsonrpc"] = datajson.get("jsonrpc")
  return finres

if __name__ == '__main__':
  # Small example of JSON-RPC processing w/o server
  def greet_handler(params, **kwargs):
    lang = params.get("lang")
    if not lang: return rpc_error("No 'lang'! ")
    if lang != "en": return rpc_error(f"Don't know how to greet in '{lang}'")
    return {"msg": "Hello !", "Lang": "en"}
  api_add("greet", greet_handler)
  req1 = {"method": "greet", "params": {"lang": "en"}}
  req2 = {"method": "greet", "params": {"lang": "cn"}}
  req3 = {"random": 5.6799, "crap": True}
  reqok = req_is_rpc(req1)
  print(f"RPC format OK: {reqok}")
  r = dispatch(req1)
  print("R1: ", r)
  reqok = req_is_rpc(req2)
  print(f"RPC format OK: {reqok}")
  r = dispatch(req2)
  print("R2: ", r)
  reqok = req_is_rpc(req3)
  print(f"RPC format OK: {reqok}")
  exit(0)
