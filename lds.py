#!/usr/bin/env python3
# Simple LDAP client and reusable building blocks
# for createing more advanced utilities / applications.

#Note: Deduplicates a list while preserving exact discovery order
# unique_ordered_dns = list(dict.fromkeys(raw_dn_list))

import ssl
import ldap3
import json
from ldap3 import Server, Connection, Tls, BASE, LEVEL, SUBTREE
from ldap3.core.exceptions import LDAPException
import re
import sys
  
# Config for connection, bind, and schema parameters
LDAP_CONFIG_EXAMPLE = {
  "hosturl": "ldaps://ldap.example.com:636",
  "user": "cn=read-only-admin,dc=example,dc=com",  # Supports DN, UPN (user@domain), or SAM
  "bindpass": "SuperSecretPassword123!",
  "member_attr": "uniqueMember",		   # Configurable: e.g., 'member', 'uniqueMember'
  "travre": "", # User Member traversal avoidance
  #"debug": 1,
  "idattr": "", # e.g. "uid"
  # Used to distinguish nested groups from users
  #"group_ocs": {
  #    "groupofuniquenames": True,
  #    "groupofnames": True, # AD
  #    "group": True,
  #    "posixgroup": True, # AD,POSIX
  #},
  #"verify_ssl": True,				    # Set to False for self-signed test certs
  "memsaslist": False,
}
# Good universal list of group OC:s. sambaGroupMapping (can have mems?) ? 
group_ocs_def = {
  "groupofuniquenames": True,
  "groupofnames": True,
  "group": True, # AD typical (DN)
  "posixgroup": True,
}
# Add or Delete (add/del) an OC from group_ocs_def
def add_group_ocs(ocslist, op='add'): # 
  for oc in ocslist:
    if   op == 'add': group_ocs_def[oc] = True
    elif op == 'del': group_ocs_def.pop(oc, None) # Note: added "None" never throws KeyError

# Establishes and binds an LDAP connection using the configuration dictionary. create_ldap_connection
def ld_conn(config: dict) -> Connection:
  tls_config = ldap3.Tls( validate=ssl.CERT_REQUIRED if config.get("verify_ssl", False) else ssl.CERT_NONE )
  
  server = ldap3.Server( config["hosturl"], use_ssl=config["hosturl"].lower().startswith("ldaps://"), tls=tls_config, get_info=None)
  
  # auto_bind=True immediately opens the socket and performs the bind operation
  bindpass = config.get("bindpass") or config.get("pass")
  #user = config.get("user")
  conn = ldap3.Connection( server, user=config["user"], password=bindpass, auto_bind=True, raise_exceptions=True)
  return conn

# Normalize a DN for reliable deduplication and cycle (circular references) tracking.
def normalize_dn(dn: str) -> str:
  return dn.strip().lower()

# Initialize traversing stats.
# This is also nice/easy way to reset the stats between 2 traversals
def trav_stats():
  s = {}
  # Groups w. no members
  s["grpcnt"] = s["usercnt"] = s["remcnt"] = s["grpemtycnt"] = 0
  s["grpemtycnt"] = -1
  return s
# Output various info statistics on connection
def lds_errinfo(conn, cfg=None):
  if cfg: print(f"Server {cfg.get('hosturl')} conn info");
  print("bound:", conn.bound)
  print("closed:", conn.closed)
  print("last_error:", conn.last_error)
  print("result:", conn.result)
# Recursively traverse an LDAP group and collect members from depth pf traversed tree.
# Handles circular group nesting safely.
# return a deduplicated set of non-group member DNs
def get_flattened_group_members(conn: ldap3.Connection, root_group_dn: str, config: dict ) -> set[str]:
  member_attr = config.get("member_attr") or config.get("memattr") # defaulted to "uniqueMember"
  if not member_attr: member_attr = "uniqueMember"
  group_ocs = config.get("group_ocs", group_ocs_def); # set()
  if not group_ocs: print(f"No group object classes found (Must have)!"); return;
  group_classes = { oc.lower() for oc in group_ocs }

  visited_groups = set()   # Track normalized group DNs to prevent circular loops
  leaf_members = set()     # Store final deduplicated member DNs (preserves original casing via map)
  dn_case_map = {}	   # Maps normalized_dn -> original_dn for clean output
  
  travre = config.get("travre") if config.get("travre") else None # speedup
  # travre = re.compile(config.get("travre"), re.IGNORECASE) # Later: travre.search(current_dn)
  debug  = config.get("debug")
  #OLD: stats = config.get("stats", {"ucnt": 0})
  stats  = config.get("stats")
  idattr = config.get("idattr")
  sattrs = ["objectClass", member_attr]
  if idattr: sattrs.append(idattr)
  if debug: print("Search attrs: ", sattrs);
  def _traverse(current_dn: str):
    norm_current = normalize_dn(current_dn)
    if debug: print(f"Enc: {norm_current} ... check patt ('{travre}') / search");
    # Cycle prevention: skip if we have already inspected this group
    if norm_current in visited_groups: return
    # Option "travre", traversal Regexp. See if we can recognize non-group and avoid fetching it (just store member DN)
    # Drops e.g. real: 2.9s => 0.3s. TODO: Allow complement (MUST NOT MATCH to traverse, e.g ou=people, ...)
    if travre and not re.search(travre, current_dn): # print(f"RE-SKIP (not {travre})");
      dn_case_map[norm_current] = str(current_dn)
      stats["remcnt"] += 1
      return # Before return MUST collect member (above)!
    # Query the specific entry at BASE scope to inspect its objectClass and member attribute
    if debug: print(f"Actually  search (BDN) '{current_dn}'...");
    try:
      conn.search( search_base=current_dn, search_filter="(objectClass=*)", search_scope=ldap3.BASE, attributes=["objectClass", member_attr] )
    except LDAPException as e:
      import traceback
      traceback.print_exc()
      lds_errinfo(conn, config);
      print(f"[WARN] Search threw trying to find entry by DN '{current_dn}': {e}")
      return

    if not conn.entries: print(f"Stale DN - No (0) entries by DN {current_dn}"); return

    entry = conn.entries[0] # There will always be one by DN
    entry_classes = { str(oc).lower() for oc in entry["objectClass"].values } if "objectClass" in entry else set()

    # Check if the current entry is a group (both sets)
    is_group = bool(entry_classes.intersection(group_classes))

    if is_group:
      visited_groups.add(norm_current)
      if stats: stats["grpcnt"] += 1
      if debug: print(f"GROUP: Check memattr '{'member_attr'}' for presence and vals")
      # Extract members if the attribute exists and is populated
      if member_attr in entry and entry[member_attr].values:
        for target_dn in entry[member_attr].values:
          target_dn_str = str(target_dn).strip()
          # Some LDAP servers put an empty string or dummy DN in empty uniqueMember fields
          if not target_dn_str: continue
          norm_target = normalize_dn(target_dn_str)
          # If already known as a visited group or collected leaf member, skip LDAP lookup
          if norm_target in visited_groups or norm_target in dn_case_map: continue
          _traverse(target_dn_str)
    # User ! Note: We can gather any unique/ID attribute here by cfg "idattr"
    else:
      if stats: stats["usercnt"] += 1
      # Single *first* value: value = entry["mail"].value OR entry.mail.value
      # Multi (list): entry.memberOf.values
      # Also: d = entry.entry_attributes_as_dict
      if idattr and idattr in entry: dn_case_map[norm_current] = entry[idattr].value; return
      # Entry is a leaf member (e.g., user, computer, service account)
      dn_case_map[norm_current] = str(entry.entry_dn)
  #print("")
  # Start recursion from the root group
  _traverse(root_group_dn)

  # Return original-cased DNs for all discovered leaf members
  leaf_members = set(dn_case_map.values()) # Note: .values() - Original raw LDAP values (DN or idattr)
  # TODO: Option for set() or list:
  #return sorted(leaf_members) # if config.get("memsaslist") else leaf_members
  print("Stats: ", stats)
  return leaf_members

def qp_ldscomm(cfg, qprof, **kwargs):
  import copy
  cfg2 = copy.deepcopy(cfg)
  cfg2.pop("base") # eliminate: TypeError: str.format() got multiple values for keyword argument 'base'
  return "ldapsearch -LLL -H '{hosturl}' -b '{base}' -w '{passwd}' -D '{user}' '{filter}'".format(**qp, **cfg2)

# Resolves "base" for "bid" - Base id
def mkquery(cfg, qprof):
  bid = cfg.get("defbid") or "root" # Base id (e.g.): root,sa,user,group,mach
  bases = cfg.get("bases")
  if not bases or not isinstance(bases, dict): usage("No bases for lookup")
  if qprof.get("bid"): bid = qprof.get("bid")
  base = bases.get(bid)
  # if not base: base = cfg.get("ubase")
  qprof["base"] = base

# Find entry for DN, returning (Only) DN.
# Search from ultimate base with always SUBTREE scope (Others: BASE, LEVEL, SUBTREE).
# Only fetch objectclass attribute (always present)
# Example: dn = lds.find_for_dn(conn, cfg, f"(cn={grpname})")
def find_for_dn(conn, cfg, sfilter):
  conn.search(search_base=cfg.get("base"), search_filter=sfilter, search_scope=ldap3.SUBTREE, attributes=["objectclass"])
  if not conn.entries: return None
  #for entry in conn.entries:
  return conn.entries[0].entry_dn
# TODO: Only cfg
def query_by_prof(conn, cfg, qp):
  mkquery(cfg, qp)
  print("QUERY-PROF: ", qp, file=sys.stderr)
  #filter = "(CN=)" # in ",OU=Serv..."
  attrs = ['*'] # , "memberOf"] # None # ['cn', 'mail']
  # "bid": "group" 
  #attrs = []
  # success, result, response, request => for entry in response: (Now entry is dict !!!)
  # success, result, response, request =
  #try:
  conn.search(search_base=qp.get("base"), search_filter=qp.get("filter"), attributes=attrs) # search_scope='BASE',
  #except LDAPException as e:
  #  ...
  # Print entries. Has entry_to_json() or entry_to_ldif() methods
  if not len(conn.entries):
    print(f"No results from '{base}' by filter '{filter}' (base_id: {bid}, scope: ...) !".format(**qp), file=sys.stderr)
    return None # OR [] ?
  # TODO: Only return result (see return value info above) or conn.entries ?
  eset = [] # Collect here
  for entry in conn.entries:
  # Store here ...
  #for entry in response:
    #print(entry.uid, entry.mail) # cn
    print(entry.entry_to_ldif())
    #print(entry.entry_to_json())
    #eset.append(entry)
  return eset

if __name__ == "__main__":
  import ldap_config
  cfg = ldap_config.LDAP_CONFIG # Config from ldap_config.py w. module-global LDAP_CONFIG
  if len(sys.argv) < 2: print(f"Pass DN (to traverse) as first arg."); exit(1)
  target_group_dn = sys.argv[1] # e.g. "cn=engineering-all,ou=groups,dc=example,dc=com"
  #print(sys.argv)
  
  #print(cfg)
  #if len(sys.argv) < 2: usage(f"No subcommand passed!");exit(1)
  #op = sys.argv.pop(1)
  #args = parser.parse_args()
  #opts = vars(args)
  #opts["op"] = op
  #print(f"OPTS: {opts}"); # exit(1)
  #if opts.get("bid"): opts["bid"] =
  #opn = next((opn for opn in ops if opn.get('id') == op), None)
  #if not opn: print(f"No subcomm. {op} supported");exit(1)
  #opn.get("cb")(opts)
  try:
    print(f"Connecting to {cfg['hosturl']} as {cfg['user']}...")
    conn = ld_conn(cfg) # LDAP_CONFIG
    print(f"Traversing group tree starting at: {target_group_dn}\n")
    members = get_flattened_group_members(conn, target_group_dn, cfg) # LDAP_CONFIG
    print(f"Total unique leaf members found: {len(members)}")
    for idx, member_dn in enumerate(sorted(members), start=1):
      print(f"  {idx}. {member_dn}")

  except LDAPException as err:
    print(f"[ERROR] LDAP operation failed: {err}")
