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
import sys
  
# Config for connection, bind, and schema parameters
LDAP_CONFIG_EXAMPLE = {
  "hosturl": "ldaps://ldap.example.com:636",
  "user": "cn=read-only-admin,dc=example,dc=com",  # Supports DN, UPN (user@domain), or SAM
  "bindpass": "SuperSecretPassword123!",
  "member_attr": "uniqueMember",		   # Configurable: e.g., 'member', 'uniqueMember'
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
  "group": True,
  "posixgroup": True,
}
#def add_group_ocs(ocslist):
#   group_ocs_def
# Establishes and binds an LDAP connection using the configuration dictionary. create_ldap_connection
def ld_conn(config: dict) -> Connection:
  tls_config = ldap3.Tls( validate=ssl.CERT_REQUIRED if config.get("verify_ssl", False) else ssl.CERT_NONE )
  
  server = ldap3.Server( config["hosturl"], use_ssl=config["hosturl"].lower().startswith("ldaps://"), tls=tls_config, get_info=None)
  
  # auto_bind=True immediately opens the socket and performs the bind operation
  bindpass = config.get("bindpass") or config.get("pass")
  conn = ldap3.Connection( server, user=config["user"], password=config["bindpass"], auto_bind=True, raise_exceptions=True)
  return conn

# Normalize a Distinguished Name for reliable deduplication and cycle tracking.
def normalize_dn(dn: str) -> str:
  return dn.strip().lower()

# Recursively traverse an LDAP group and returns a deduplicated set of non-group member DNs.
# Handles circular group nesting safely.
def get_flattened_group_members(conn: Connection, root_group_dn: str, config: dict ) -> set[str]:
  member_attr = config.get("member_attr") or config.get("memattr") # defaulted to "uniqueMember"
  if not member_attr: member_attr = "uniqueMember"
  group_ocs = config.get("group_ocs", group_ocs_def); # set()
  group_classes = { oc.lower() for oc in group_ocs }

  visited_groups = set()   # Track normalized group DNs to prevent circular loops
  leaf_members = set()     # Store final deduplicated member DNs (preserves original casing via map)
  dn_case_map = {}	   # Maps normalized_dn -> original_dn for clean output
  stats = config.get("stats", {"ucnt": 0})
  def _traverse(current_dn: str):
    norm_current = normalize_dn(current_dn)

    # Cycle prevention: skip if we have already inspected this group
    if norm_current in visited_groups: return
    # Query the specific entry at BASE scope to inspect its objectClass and member attribute
    try:
      conn.search( search_base=current_dn, search_filter="(objectClass=*)", search_scope=BASE, attributes=["objectClass", member_attr] )
    except LDAPException as e:
      print(f"[WARN] Could not read DN '{current_dn}': {e}")
      return

    if not conn.entries: return

    entry = conn.entries[0] # There will always be one by DN
    entry_classes = { str(oc).lower() for oc in entry["objectClass"].values } if "objectClass" in entry else set()

    # Check if the current entry is a group (both sets)
    is_group = bool(entry_classes.intersection(group_classes))

    if is_group:
      visited_groups.add(norm_current)

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
    # User !
    else:
      stats["ucnt"] += 1
      # Entry is a leaf member (e.g., user, computer, service account)
      dn_case_map[norm_current] = str(entry.entry_dn)
  #print("")
  # Start recursion from the root group
  _traverse(root_group_dn)

  # Return original-cased DNs for all discovered leaf members
  leaf_members = set(dn_case_map.values())
  # TODO: Option for set() or list:
  #return sorted(leaf_members) # if config.get("memsaslist") else leaf_members
  print("Stats: ", stats)
  return leaf_members

def mkquery(cfg, qprof):
  bid = cfg.get("defbid") or "root" # Base id (e.g.): root,sa,user,group,mach
  bases = cfg.get("bases")
  if not bases or not isinstance(bases, dict): usage("No bases for lookup")
  if qprof.get("bid"): bid = qprof.get("bid")
  base = bases.get(bid)
  # if not base: base = cfg.get("ubase")
  qprof["base"] = base

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
  conn.search(search_base=qp.get("base"), search_filter=qp.get("filter"), attributes=attrs) # search_scope='BASE',
  # Print entries. Has entry_to_json() or entry_to_ldif() methods
  if not len(conn.entries): usage(f"No results from '{base}' by filter '{filter}' (base_id: {bid}, scope: ...) !".format(**qp))
  eset = []
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
  cfg = ldap_config.LDAP_CONFIG
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
    ldap_conn = ld_conn(cfg) # LDAP_CONFIG
    print(f"Traversing group tree starting at: {target_group_dn}\n")
    members = get_flattened_group_members(ldap_conn, target_group_dn, cfg) # LDAP_CONFIG
    print(f"Total unique leaf members found: {len(members)}")
    for idx, member_dn in enumerate(sorted(members), start=1):
      print(f"  {idx}. {member_dn}")

  except LDAPException as err:
    print(f"[ERROR] LDAP operation failed: {err}")
