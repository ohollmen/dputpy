#!/usr/bin/env python3
# # Log data collector for line based logs.
# Collects data from log into single dictionary (which can be
# hierarchical if callbacks so desire and start forming a hierarchy to it).
# Works on "matchers" that are combo of:
# - RE Pattern (to match the line with)
# - Callback to populate match toto
# ## Notes
# - It is recommended that "patt" RE is stored in single quotes
#   for minimum escaping (withing python code, if matchers are stored in
#   )
import re
import sys

# Example matcher callbacks.
# Signature for "cb": def hld_line(line, match_list, ctx).
# Some of these example matchers might actually be useful in real applications.
# Callback could return whether to stop or not (stop = True).
def hdl_bool(line, mlist, ctx):
  if len(mlist) > 1: ctx[mlist[1]] = True if mlist[2] == 'True' else False
  # Secondary match within same line !!
  # Note: The match (m) composition differs between re.search(restr, mstr) recomp.search(mstr) !!!
  m = re.search(r'\bextra:\s+(\w+)', line)
  if m and len(m.groups()): ctx["extra"] = m[1]
def hdl_dotnot(line, mlist, ctx):
  if len(mlist) > 1: ctx["action"] = mlist[1] # jenkins.* (validate actions/methods here ?)
def hdl_keyval(line, mlist, ctx):
  if len(mlist) > 2: ctx[mlist[1]] = mlist[2]
def hdl_multival(line, mlist, ctx):
  key = mlist[1]
  #print(f"Assign multival {mlist[2]} to key: {key}")
  # Assume 
  lval = ctx.get(key)
  if not lval or not isinstance(lval, list): ctx[key] = []
  ctx[key].append(mlist[2])
  return
# Note: the order of matcher will (dramatically) affect the ctx output as the
# first matcher used on line stops further matching. Order your entries smartly / carefully !
test_matchers = [ # Need case sensitive opt/flag ("opts" ORred) ?
  {"patt": r'(multi\w+):\s+(.+)', "cb": hdl_multival, "term": False},
  # For some reason \b translates to \x08
  {"patt": r'(\w+):\s(True|False)', "cb": hdl_bool, "term": False},
  {"patt": r'(\w+\.\w+):\s+(.+)', "cb": hdl_dotnot, "term": False},
  
  {"patt": r'(\w+):\s+(.+)', "cb": hdl_keyval, "term": False},
  
]

def matchers_init(matchers, **kwargs):
  # Init matchers by compiling regexp
  debug = kwargs.get('debug')
  for matcher in matchers:
    # Compile Regexp
    if debug: print(f"Compiling '{matcher['patt']}'");
    matcher["re"] = re.compile(matcher["patt"]) # 2nd options, e.g. re.IGNORECASE / re.I
    # Other inits ?
# Perform Log Scan / Data collection
# Assume all required members to be present in matcher
# kwargs parameters:
# - ctx - (pre-filled) context (dict) to collect data to
def log_scan(matchers, lines, **kwargs):
  matchers_init(matchers, **kwargs)
  actctx = {} if (not kwargs.get("ctx")) else kwargs.get("ctx")
  if debug: print("Initial ctx: ", actctx);
  i = 0
  for line in lines:
    i += 1
    if not line: continue
    if debug > 1: print(f"Line: '{line}'. Try {len(matchers)} matchers.");
    # Try every matcher
    j = 1
    term = 0
    for matcher in matchers:
      j += 1
      if debug: print(f"- Run RE{j}: {matcher['patt']}");
      m = matcher["re"].search(line)
      if m and debug: print(f"- MATCH({j}): {m.groups()}");
      if m: # The m is of type re.Match
        if debug: print(f"- Matched line({i}) '{line}' (by '{matcher['patt']}') - Call cb ({type(matcher['cb'])})")
        mgs = list(m.groups()); mgs.insert(0, "")
        rc = matcher["cb"](line, mgs, actctx) # Match took place, call "cb", Note: rc still unused
        if matcher.get("term"): term = 1 # Stop/Terminate whole file parsing at this match
        break # Do not try any other matchers
    if term: break
  return actctx # All info acqired from logs (in dict) !



if __name__ == "__main__":
  import json
  fn =  sys.argv[1] if len(sys.argv) > 1 else "tdata/linelog.txt" # ""
  debug = 0
  print(f"main: Work on file: {fn}")
  
  lines = open(fn, "r").read().split("\n")
  if debug > 3: print("LINES:", lines)
  results = {"just_a_key": "just_a_val", "multival": True}
  print("START: ", json.dumps(results, indent=2))
  log_scan(test_matchers, lines, ctx=results, debug=debug);
  print("END: ", json.dumps(results, indent=2))
