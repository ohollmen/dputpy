#!env python3
# Create SSL certs with `openssl req` (man openssl-req).
# Also see: man openssl-format-options (1)
# Refs:
# - Very good config examples: https://www.ibm.com/docs/en/hpvs/1.2.x?topic=reference-openssl-configuration-examples
# - Example usage context: https://vnuggets.com/2019/08/08/ansible-certificate-authentication-to-windows/
# - Example of "[v3_ca]" https://medium.com/@dngrhm/if-you-are-getting-the-error-error-loading-extension-section-v3-ca-on-macos-follow-the-comment-d3c5bf275356
# NEW
# - https://docs.devolutions.net/kb/general-knowledge-base/secure-self-signed-certificates/
import jinja2
import os

# SSL Config. The more Cert-required properties there is present here
# (preferably all), the less interactivity there will be on `openssl req`.
# 
conftmpl = '''
[req]
prompt                 = no
days                   = 365
# References to sections
distinguished_name     = req_distinguished_name
req_extensions         = v3_req
[ req_distinguished_name ]
countryName            = {{ country }}
stateOrProvinceName    = {{ state }}
localityName           = {{ locality }}
organizationName       = {{ org }}
organizationalUnitName = {{ orgunit }}
commonName             = {{ cn }}
emailAddress           = {{ email }}
[ v3_req ]
# false => NOT a CA Certificate
basicConstraints       = CA:false
# serverAuth/clientAuth
extendedKeyUsage       = {{ authtype }}
# With '@' can refer to a section
subjectAltName         = @sans
[ sans ]
DNS.0 = localhost
DNS.1 = myexampleclient.com
'''


if __name__ == '__main__':
  # export OPENSSL_CONF=openssl.conf
  # os.environ["USER"] os.environ.get("USER")
  template = jinja2.Template(conftmpl)
  # TODO (?): Assemble DN here, pass with -subj
  p = {"country":"US", "state":"NY", "locality":"New York",
    "org":"My Company", "orgunit":"My Unit",
    "authtype":"clientAuth",
    "cn": "thecompany.com",
    "email": "me.here@mycompany.com", # 
     "ver": 1}
  # ppp = passphrase parameter
  preq = {"days": 365, "username": os.environ["USER"], "outpath": "/tmp/",
    "extsectname": "v3_req"}
  # Test version by `openssl version` OpenSSL 1.1.1 / OpenSSL 3.2.1
  preq["ppp"] = "noenc" if p["ver"] == 3 else "nodes"
  out = template.render(**p)
  # Save
  fname = "/tmp/openssl."+str(os.getpid())+".conf"
  fh = open(fname, "w")
  fh.write(out)
  fh.close()
  os.environ["OPENSSL_CONF"] = fname
  print("Create cert by "+out)
  print("To file "+fname)
  # Run openssl
  # Notes:
  # - Param `-extensions v3_req_client` refers to a config section, which MUST exist!
  # (Section will have (e.g.) extendedKeyUsage, subjectAltName, here v3_req)
  # - Param (e.g.) -subj '/CN={{ username }}' will *completely* set / override the (whole) CN
  #  formulation, disgarding the config file.
  # - Left out: -subj '/CN={{ username }}'
  # - consider: -CA
  # - -x509 option implies -new if -in is not given
  reqtmpl = "openssl req -x509 -{{ ppp }} -days {{ days }} -newkey rsa:2048 -out {{ outpath }}/cert.pem -outform PEM -keyout {{ outpath }}/cert_key.pem  -extensions {{extsectname}}"
  template_r = jinja2.Template(reqtmpl)
  out = template_r.render(**preq)
  print("To create Run: "+out)
  print("To verify Run: "+"openssl x509 -in /tmp/cert.pem -text -noout")
