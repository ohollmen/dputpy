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

# Config for connection, bind, and schema parameters
LDAP_CONFIG_EXAMPLE = {
  "hosturl": "ldaps://ldap.example.com:636",
  "user": "cn=read-only-admin,dc=example,dc=com",  # Supports DN, UPN (user@domain), or SAM
  "bindpass": "SuperSecretPassword123!",
  "member_attr": "uniqueMember",		   # Configurable: e.g., 'member', 'uniqueMember'
  # Used to distinguish nested groups from users
  "group_object_classes": {
      "groupofuniquenames": True,
      "groupofnames": True,
      "group": True,
      "posixgroup": True,
  },
  #"verify_ssl": True,				    # Set to False for self-signed test certs
  "memsaslist": False,
}

# Establishes and binds an LDAP connection using the configuration dictionary.
def create_ldap_connection(config: dict) -> Connection:
  tls_config = ldap3.Tls( validate=ssl.CERT_REQUIRED if config.get("verify_ssl", False) else ssl.CERT_NONE )
  
  server = ldap3.Server( config["hosturl"], use_ssl=config["hosturl"].lower().startswith("ldaps://"), tls=tls_config, get_info=None)
  
  # auto_bind=True immediately opens the socket and performs the bind operation
  conn = ldap3.Connection( server, user=config["user"], password=config["bindpass"], auto_bind=True, raise_exceptions=True)
  return conn

# Normalize a Distinguished Name for reliable deduplication and cycle tracking.
def normalize_dn(dn: str) -> str:
  return dn.strip().lower()

# Recursively traverse an LDAP group and returns a deduplicated set of non-group member DNs.
# Handles circular group nesting safely.
def get_flattened_group_members(conn: Connection, root_group_dn: str, config: dict ) -> set[str]:
  member_attr = config.get("member_attr", "uniqueMember")
  group_classes = { oc.lower() for oc in config.get("group_object_classes", set())}

  visited_groups = set()   # Track normalized group DNs to prevent circular loops
  leaf_members = set()     # Store final deduplicated member DNs (preserves original casing via map)
  dn_case_map = {}	   # Maps normalized_dn -> original_dn for clean output

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
      # Entry is a leaf member (e.g., user, computer, service account)
      dn_case_map[norm_current] = str(entry.entry_dn)

  # Start recursion from the root group
  _traverse(root_group_dn)

  # Return original-cased DNs for all discovered leaf members
  leaf_members = set(dn_case_map.values())
  # TODO: Option for set() or list:
  #return sorted(leaf_members) # if config.get("memsaslist") else leaf_members
  return leaf_members


if __name__ == "__main__":
  import ldap_config
  import sys
  target_group_dn = sys.argv[1] # e.g. "cn=engineering-all,ou=groups,dc=example,dc=com"
  #print(sys.argv)
  cfg = ldap_config.LDAP_CONFIG
  print(cfg)
  try:
    print(f"Connecting to {cfg['hosturl']} as {cfg['user']}...")
    ldap_conn = create_ldap_connection(cfg) # LDAP_CONFIG
    print(f"Traversing group tree starting at: {target_group_dn}\n")
    members = get_flattened_group_members(ldap_conn, target_group_dn, cfg) # LDAP_CONFIG
    print(f"Total unique leaf members found: {len(members)}")
    for idx, member_dn in enumerate(sorted(members), start=1):
      print(f"  {idx}. {member_dn}")

  except LDAPException as err:
    print(f"[ERROR] LDAP operation failed: {err}")
