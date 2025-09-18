# for AWS launch mechanisms
import sys
import requests
import base64
import json
import logging
import re
#logger = logging.getLogger(__name__)

# AWS Documented URLs to call from a running container to retrieve an SQS Message.
# https://docs.aws.amazon.com/lambda/latest/dg/runtimes-api.html
# AWS Port for next / response / response calls is 9001
url_sqs_next = "http://127.0.0.1:{port}/2018-06-01/runtime/invocation/next" # GET
# Use value from 'next' call response http headers 'Lambda-Runtime-Aws-Request-Id' (In AWS docs URL: /AwsRequestId/ or /$REQUEST_ID/ )
url_sqs_resp = "http://127.0.0.1:{port}/2018-06-01/runtime/invocation/{request_id}/response" # POST: Note: reqires .format()
# Error during processing SQS Message
url_sqs_err  = "http://127.0.0.1:{port}/2018-06-01/runtime/invocation/{request_id}/error" # POST
urls = { "next": url_sqs_next, "resp": url_sqs_resp, "err": url_sqs_err }
# Note: There are a few potential URL:s that may be needed for granular scenarios
# /runtime/init/error
port = 9001 # "Module/Package" level default. Change by sqsl.port Before calling URL generation functions.
url_self = "http://127.0.0.1:{port}/"
# echo -n '{"message": "Hello"}' | base64
cev_b64_str = "eyJtZXNzYWdlIjogIkhlbGxvIn0="
sqs_ev_mock = {"Records": [{"messageId": "6ccf123", "body": cev_b64_str } ] }
debug = 0

# Generate URL (and validate parameters to format it fully).
# Port (default: 9001) can be passed in kwargs but it will fall back to package level "port" var.
# rep and err call types must have "request_id".
# Return URL (or raise exceptions for lac
def sqs_url(bn, **kwargs):
  p = kwargs.get("port")
  if not p: p = port
  if not bn in urls: raise f"URL type (basename) '{bn}' not in allowed URL types"
  rtypes = ["resp","err"]
  if (bn in rtypes) and (not "request_id" in kwargs): raise "sqs_url(): No request_id kwarg for response/error call !"
  return urls[bn].format(port=p, request_id=kwargs.get('request_id', ""))

# Parse Cloud event JSON message embedded (as b64) from an AWS SQS message passed here.
# Expects AWS SQS message w. Records[0].body containing the b64 
# Base64 encoding is decoded and the resulting JSON is parsed and returned (for any potentially useful "other" SQS message data
# access it at the caller - this methond *only* deals w. Cloud event).
# Return Cloud event J(JSON) data structure and None on various failures during JSON b64-extraction and parsing.
def sqs_msg_data_json(sqsevent): # SQS Event with std. structure
  #marr = sqsevent.get("Records")
  recs0 = sqsevent.get("Records", [])[0] # [{}]
  if not recs0: logger.info("No recs0 found"); return None
  if len(sqsevent.get("Records")) > 1: print("Warming: More than 1 message in request !!!");
  #cev_b64_str = sqsevent.get("Records", [{}])[0].get("body", "{}")
  cev_b64_str = recs0.get("body", None)
  # SQS requires min 1 byte !
  if not cev_b64_str: print("No b64 enc 'body' found"); return None
  # validate as SQS message / event
  mid = recs0.get("messageId")
  if not mid: print("No 'messageId' found"); return None
  # NEW: Heuristically accept either raw (escaped within json) json or b64 encoded json in "body".
  j_str = None
  if cev_b64_str.startswith("{"):# or re.match(r'{\s*"', j_str): # automatically multiline/single string
     j_str = cev_b64_str
  #else: #
  elif re.search(r'^[A-Za-z0-9+/=]+$', cev_b64_str):
    b64_bytes = cev_b64_str.encode("utf-8")
    j_str_bytes = base64.b64decode(b64_bytes)
    j_str = j_str_bytes.decode("utf-8")
  if not j_str: print("No raw json or b64 enc. json found in member 'body'."); return None
  # cev denotes Cloud event, but this can be really any JSON data payload.
  cev = json.loads(j_str)
  if not cev: print(f"No JSON message parsed (from {j_str})"); return None
  if not isinstance(cev, dict): print(f"No dict found from JSON parsed (from {j_str})"); return None
  # Check a few members ?
  #if not cev.get("data"): print(f"No member 'data' found in CEv (from {j_str})"); return None
  #if not cev.get("attributes"): print(f"No member 'attributes' found in CEv (from {j_str})"); return None
  print(f"CEV(msgid:{mid}):", json.dumps(cev, indent=2)) # DEBUG
  return cev

# Request next event from SQS and parse message from it's .Records[0]["body"]
# The "body" is expected to be JSON content encoded into base64 (to avoid escaping hassle, all SQS
# clients should produce messages in that specific format w. JSON vals in utf-8).
# Return special object with data and meta-info on Even message (todo: itemize) or None on various failures.
def sqs_next():
  url = sqs_url('next') # Use class level port
  resp = requests.get(url)
  if not resp: print(f"No response gotten from '{url}'"); return None
  event = resp.json() # AWS SQS Event Message
  if not event: print("No JSON from SQS next-call (gotten by requests HTTP)."); return None
  ctx_hdrs = resp.headers
  reqid = ctx_hdrs.get('Lambda-Runtime-Aws-Request-Id')
  if not reqid: print("No Lambda request_id in headers."); return None
  # Transform / extract here ?
  print(f"EVENT({reqid}):", json.dumps(event, indent=2))
  # print(f"EVENT({reqid}):", json.dumps(ctx_hdrs, indent=2)) # TypeError: Object of type CaseInsensitiveDict is not JSON serializable
  cev = sqs_msg_data_json(event)
  return {"sqsevent": event, "context": ctx_hdrs, "reqid": reqid, "request_id": reqid, "body_json": cev} # body_json_data ? body_data ?

# Send response (or error) to SQS for having processed event successfully (is this mandatory ?)
# An error response can be indicated by kwarg 'err' set to (any) true value.
# dict sqse MUST have member 'request_id' to template the URL (for bot resp/err).
# Return the requests http response object (for inspection at caller).
def sqs_resp(sqse, **kwargs):
  if not sqse: print("No sqse passed for URL formatting ()"); return
  if not isinstance(sqse, dict): print("No sqse passed as dict for URL formatting ()"); return
  if not sqse.get("request_id"): print("No sqse with member 'request_id' for URL formatting ()"); return
  data = 'SUCCESS'
  # urlfmt = url_sqs_resp
  calltype = 'resp'
  err = kwargs.get('error') or kwargs.get("err")
  # 'FAILURE' ?
  if err: data = 'ERROR'; calltype = 'err'; # urlfmt = url_sqs_err;
  url = sqs_url(calltype, **sqse)
  # Custom (nested) data ?
  rd = sqse.get('respdata')
  if kwargs.get('respdata'): rd = kwargs.get('respdata') # Alternatively in kwargs (by same key)
  if rd and isinstance(rd, dict): data = json.dumps(rd)
  # OLD: url = urlfmt.format(**sqse)
  hresp = requests.post(url, data=data) # json=resp) Use 'request_id'
  print(f"Sent message ACK to response (err={err}) url: {url}")
  return hresp

# Implement sqs_error in sqs_resp()
#def sqs_error(sqse):
#  return {}

# A convenience method to detect if data passed has mandatory CloudEvent properties in it.
def is_cloudevent(elope):
  msg = elope.get("message")
  if not msg: raise Exception("Top-level 'message' missing !"); # return 0
  # Note: Cannot plainly do msg.get("data") for falsy value !!! Loosen up "attributes" too (for empty dict ?)
  if not "data" in msg: raise Exception("'message' branch missing cloudevent property 'data'."); # return 0
  if not "attributes" in msg: raise Exception("'message' branch missing cloudevent property ''attributes'."); # return 0
  return 1

# Serve AWS Lambda call (triggered by SQS) to container.
# Try to avoid boto3 dependencies as we **can** receive the SQS message plainly via HTTP (requests).
# Supported kwargs:
# - cb (function) - Callback to process the
def serve_aws_lambda(**kwargs):
  #cev = sqs_msg_data_json(sqs_ev_mock)
  #if not cev: print("Failed to parse SQS message:", sqs_ev_mock)
  #exit(0)
  # while True:
  # Be ready to receive (many) ?
  debug = kwargs.get('debug')
  #try:
  sqse = sqs_next()
  if not sqse: print("No message from SQS ('next' - HTTP API)"); return
  #except Exception as e:
  #  print(f"SQS Event not properly retrieved from 'next' - web servive"); return
  # Just make a entrypoint that gets passed CEv (obj. w. attrs, data ...)!
  # requests.post(url_self.format({"port": 8081}), json=resp)
  # Process based on sqse (similar to AWS Lambda def )
  # TODO: validate as func ...
  cb = kwargs.get('cb')
  if not cb or not callable(cb): print("Callback for processing the SQS message data missing (or not callable type)!"); return
  rv = None
  # err = None
  respkw = {"err": 0}
  try:
    rv = cb(sqse)
  except Exception as e:
    respkw["err"] = 1
    #
  # Use rv to repond ?
  #if kwargs.get("userv"): 
  sqs_resp(sqse, **respkw)
  #exit(0)
# OLD:
# Launch Web application ? Would need to run as subprocess or multiprocessing.
#app.run() # Need to sleep ?
# Send exact cloud event
# TODO: Dont make a http call.

if __name__ == '__main__':
  print("Running main ...")
  if len(sys.argv) > 1: op = sys.argv.pop(1)
  cev = sqs_msg_data_json(sqs_ev_mock)
  print("Out from 'body' comes: ", cev);
  exit(0)
