# for AWS launch mechanisms
import sys
import requests
import base64
import json
import logging
#logger = logging.getLogger(__name__)

# AWS Documented URLs to call from a running container to retrieve an SQS Message.
# https://docs.aws.amazon.com/lambda/latest/dg/runtimes-api.html
url_sqs_next = "http://127.0.0.1:9001/2018-06-01/runtime/invocation/next" # GET
url_sqs_resp = "http://127.0.0.1:9001/2018-06-01/runtime/invocation/{request_id}/response" # POST: Note: reqires .format()
url_self = "http://127.0.0.1:{port}/"
# echo -n '{"message": "Hello"}' | base64
cev_b64_str = "eyJtZXNzYWdlIjogIkhlbGxvIn0="
sqs_ev_mock = {"Records": [{"messageId": "6ccf123", "body": cev_b64_str } ] }

# Parse Cloud event JSON message embedded (as b64) from an AWS SQS message passed here.
# Expects AWS SQS message w. Records[0].body containing the b64 
# Base64 encoding is decoded and the resulting JSON is parsed and returned (for any potentially useful "other" SQS message data
# access it at the caller - this methond *only* deals w. Cloud event).
# Return Cloud event J(JSON) data structure and None on various failures during JSON b64-extraction and parsing.
def sqs_msg_data_json(sqsevent): # SQS Event with std. structure
  recs0 = sqsevent.get("Records", [])[0] # [{}]
  if not recs0: logger.info("No recs0 found"); return None
  #cev_b64_str = sqsevent.get("Records", [{}])[0].get("body", "{}")
  cev_b64_str = recs0.get("body", None)
  if not cev_b64_str: print("No b64 enc 'body' found"); return None
  # validate as SQS message / event
  reqid = recs0.get("messageId")
  if not reqid: print("No reqid ('messageId') found"); return None
  b64_bytes = cev_b64_str.encode("utf-8")
  j_str_bytes = base64.b64decode(b64_bytes)
  j_str = j_str_bytes.decode("utf-8")
  cev = json.loads(j_str)
  if not cev: print(f"No JSON parsed (from {j_str})"); return None
  if not isinstance(cev, dict): print(f"No dict found from JSON parsed (from {j_str})"); return None
  # Check a few members ?
  #if not cev.get("data"): print(f"No member 'data' found in CEv (from {j_str})"); return None
  #if not cev.get("attributes"): print(f"No member 'attributes' found in CEv (from {j_str})"); return None
  print(f"CEV({reqid}):", json.dumps(cev, indent=2)) # DEBUG
  return cev

# Request next event from SQS and parse message from it's .Records[0]["body"]
# The "body" is expected to be JSON content encoded into base64 (to avoid escaping hassle, all SQS
# clients should produce messages in that specific format w. JSON vals in utf-8).
# Return special object with data and meta-info on Even message (todo: itemize) or None on various failures.
def sqs_next():
  resp = requests.get(url_sqs_next)
  event = resp.json() # AWS SQS Event Message
  ctx_hdrs = resp.headers
  reqid = ctx_hdrs.get('Lambda-Runtime-Aws-Request-Id')
  # if not reqid: return None
  # Transform / extract here ?
  print(f"EVENT({reqid}):", json.dumps(event, indent=2))
  print(f"EVENT({reqid}):", json.dumps(ctx_hdrs, indent=2))
  cev = sqs_msg_data_json(event)
  return {"event": event, "context": ctx_hdrs, "reqid": reqid, "body_json": cev}

# Send response to SQS for having processed event successfully (is this mandatory ?)
# dict sqse MUST have member 'request_id' to template the URL.
def sqs_resp(sqse):
  if not sqse: print("No sqse passed for URL formatting ()"); return
  if not isinstance(sqse, dict): print("No sqse passed as dict for URL formatting ()"); return
  if not sqse.get(""): print("No sqse with member 'request_id' for URL formatting ()"); return
  #resp = {"msg":"123"}
  requests.post(url_sqs_resp.format(**sqse), data='SUCCESS') # json=resp) Use 'request_id'
  return

# Serve AWS Lambda call (triggered by SQS) to container.
# Try to avoid boto3 dependencies as we **can** receive the SQS message plainly via HTTP (requests)
def serve_aws_lambda(**kwargs):
  cev = sqs_msg_data_json(sqs_ev_mock)
  if not cev: print("Failed to parse SQS message:", sqs_ev_mock)
  exit(0)
  # while True:
  # Be ready to receive
  sqse = sqs_next()
  # Launch SEDA
  #app.run() # Need to sleep ?
  # Send exact cloud event
  requests.post(url_self.format({"port": 8081}), json=resp)
  # Process based on sqse (similar to AWS Lambda def )

  sqs_resp(sqse)
  exit(0)

if __name__ == '__main__':
  print("Running main ...")

  exit(0)
