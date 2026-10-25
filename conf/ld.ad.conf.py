# Example transform to suit ones directory environment:
# - perl -pi -e 's/\bcompany\b/acme/' ld.ad.conf.py (or similar sed)
# - review DN paths for any local customizations, tweak appropriately.
cfg = {
  "id": "ad",
  "hosturl": "ldaps://ad.company.com:3269",
  # Bind user identity can have colorful variations across different LDAP servers
  # Username: mrsmith, Email: mrsmith@company.com, DN: cn=mrsmith,ou=company,dc=com, Win domain: COMPANY\mrsmith
  "user": "mrsmith@company.com",
  "pass": os.getenv("LDAP_BINDPW"),
  # Note, this is kinda repetition of bases.root, but for now is used by 
  "base": "DC=na,DC=company,DC=com",
  "member_attr": "member", # Typical of AD (OpenLDAP and standard LDAP envs use 
  # Traverse regexp for speeding up traversal for non-groups. By default keep empty
  "travre": "",
  #"travre": "OU=Exchange,",
  "idattr": "CN", # Typical: CN, sAMAccountName, name, NOT(for AD): "uid",
  #"debug": 1,
  # OC: group
  # AD
  "bases": {
    "user": "ou=people,dc=na,dc=company,dc=com",
    #"group": "dc=na,dc=company,dc=com", # safe bet, but less specific
    "group": "OU=Distribution Lists,OU=Exchange,DC=na,DC=company,DC=com",
    "root": "dc=na,dc=company,dc=com",
  },
  #"super": "",
}
