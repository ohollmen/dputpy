cfg = {
  "id": "stdldap",
  "hosturl": "ldaps://ldap.company.com:636",
  # OpenLDAP / STD LDAP servers prefer Full DN as identity.
  # This has to be discovered by anonymous or service account bind (e.g.):
  # ldapsearch -x -H ldap://ldap.company.com:636 -b dc=company,dc=com "(uid=mrsmith)" dn
  # OpenLDAP is usually (by default) generous about allowing this search.
  "user": "uid=mrsmith,ou=people,dc=company,dc=com",
  "pass": os.getenv("LDAP_BINDPW"),
  "base": "dc=company,dc=com",
  "defbid": "root",
  # Very typical bases
  "bases": {
    "user": "ou=people,dc=company,dc=com",
    "group": "ou=groups,dc=company,dc=com",
    # AD typically divides hierarchies geographically
    # na = North America, ap,apac = Asia Pacific, eu = Europe
    "sa": "OU=Service Accounts,DC=na,DC=company,DC=com",
    "root": "dc=company,dc=com",
  },
  # Not enabled in implementation yet and cannot be universally set
  #"scope": "sub", # base, one, sub
  "member_attr": "member", # "member", "memberuid"
  #"travre": "ou=groups,",
  "travre": "",
  "group_ocs": {
    "groupofuniquenames": True,
    "groupofnames": True,
    "group": True,
    "posixgroup": True
  },
  
},
