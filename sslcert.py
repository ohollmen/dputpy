#!env python3
# Create SSL certs with `openssl req` (man openssl-req).
# Also see: man openssl-format-options (1)
# 
# Refs:
# - Very good config examples: https://www.ibm.com/docs/en/hpvs/1.2.x?topic=reference-openssl-configuration-examples
# - Example usage context: https://vnuggets.com/2019/08/08/ansible-certificate-authentication-to-windows/
# - Example of "[v3_ca]" https://medium.com/@dngrhm/if-you-are-getting-the-error-error-loading-extension-section-v3-ca-on-macos-follow-the-comment-d3c5bf275356
# NEW
# - Google: openssl self signed certificate
# - https://docs.devolutions.net/kb/general-knowledge-base/secure-self-signed-certificates/
# - https://docs.microfocus.com/SM/9.61/Hybrid/Content/security/concepts/example_generating_a_client_certificate_with_openssl.htm
# - Single command: https://stackoverflow.com/questions/10175812/how-to-generate-a-self-signed-ssl-certificate-using-openssl

import jinja2
import os
import re
import argparse

# With old keys: for some reason "org" (key) is translated to "ORG", otherwise either long or short
  # (exact) attribute names are req'd. Otherwise 'req: Skipping unknown attribute "orgunit"'
p = {
    "C":"US", "S":"NY", "L":"New York",
    "O":"My Company", # "OU":"My Unit",
    "CN": "thecompany.com",
    "email": "me.here@mycompany.com", # 
    "authtype": "clientAuth",
    
    "sans": ["*.mycomp.com","main.mycomp.cm","1.1.1.1"],
    "ver": 1}
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
countryName            = {{ C }}
stateOrProvinceName    = {{ S }}
localityName           = {{ L }}
organizationName       = {{ O }}
# organizationalUnitName = {{ orgunit }}
commonName             = {{ CN }}
emailAddress           = {{ email }}
[ v3_req ]
# false => NOT a CA Certificate. CA:TRUE by default !
basicConstraints       = CA:false
# serverAuth/clientAuth
extendedKeyUsage       = {{ authtype }}
# With '@' can refer to a section
subjectAltName         = @sans
[ sans ]
DNS.0 = localhost
DNS.1 = myexampleclient.com
'''
# Generate opsnssl config, return file name.
def cfg_gen(p):
  template = jinja2.Template(conftmpl)
  cfgout = template.render(**p)
  # Save
  fname = "/tmp/openssl."+str(os.getpid())+".conf"
  fh = open(fname, "w")
  fh.write(cfgout)
  fh.close()
  os.environ["OPENSSL_CONF"] = fname
  print("Config to create cert by "+cfgout)
  print("To file "+fname)
  return fname

# Attributes and caseness in official cert format. Note: The OU (organizational unit)
# Has been deprecated from certs as of ~2022 (https://www.ssl2buy.com/wiki/deprecation-of-organization-unit-from-ssl-certificate)
# 2022-09-01 CAs MUST NOT include organizationalUnitName field in the Subject.
#dncomps = ["CN","orgunit","org","locality","state", "country"]
dncomps = ["C","ST","L", "O", "CN",]
# https://stackoverflow.com/questions/24255205/error-loading-extension-section-usr-cert
# Assemble DN from config params.
# DN components from dncomps are tried, in the order stored.
# later pass with -subj to openssl req command.
# Return usable DN
def form_dn(p, **kwargs):
  dn = ""
  usedncomps = dncomps
  for c in usedncomps:
    v = p.get(c)
    if not v: continue
    dn += "/"+c+"="+v
  return dn
# Generate Subject alternative names (DNS names OR wildcards OR IP addresses)
# 
def form_san(p, **kwargs):
  sans = []
  #ipre = re.
  for dns in p.get("sans", []):
    t = "DNS"
    if re.search(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', dns): t = "IP"
    sans.append(t+":"+dns);
  sansstr = ",".join(sans)
  #if kwargs.get("addkey"): sansstr = 'subjectAltName='+sansstr
  return 'subjectAltName='+sansstr

def conf_json_gen(opts, **kwargs):
  ks = p.keys()
  p2 = {}
  for k in ks:
    p2[k] = "";
  #in = kwargs["indent"];
  print(json.dumps(p2, indent=0));
ops = {
  "certcfg": {"cb": None, "title":""},
  "certcmd": {"cb": None, "title":""},
}
def usage(msg):
  if msg: print(msg);
  #print("Try subcommands");
  print("Try ops: "+", ".join(ops.keys()))
  
if __name__ == '__main__':
  # export OPENSSL_CONF=openssl.conf
  # os.environ["USER"] os.environ.get("USER")
  
  
  # Additional (e.g. runtime, openssl invocation related params.
  # TODO: Decide mems betw. p/preq. Merge to p (or other way around) ?
  preq = {"days": 3650, "username": os.environ["USER"], "outpath": "/tmp/",
    "keylen": 4096, "extsectname": "v3_req"}
  # Test version by `openssl version` OpenSSL 1.1.1 / OpenSSL 3.2.1
  
  cfgfname = cfg_gen(p)
  # Running openssl for Cert Creation
  # Notes on openssl req:
  # - Param `-extensions v3_req_client` refers to a config section, which MUST exist!
  # (Section will have (e.g.) extendedKeyUsage, subjectAltName, here v3_req)
  # - Param (e.g.) -subj '/CN={{ username }}' will *completely* set / override the (whole) CN
  #  formulation, disgarding everything about DN components the config file.
  # - Left out: -subj '/CN={{ username }}' (Example from client cert creation)
  # - consider: -CA
  # - -x509 option implies -new if -in is not given
  reqtmpl = "openssl req -x509 -{{ ppp }} -days {{ days }} -newkey rsa:2048 -out {{ outpath }}/cert.pem" + \
     " -outform PEM -keyout {{ outpath }}/cert_key.pem  -extensions {{extsectname}}"
  # subjectAltName=DNS:example.com,DNS:*.example.com,IP:10.0.0.1
  # /CN=example.com (subj)
  reqtmpl = "openssl req -x509 -days {{ days }} -newkey rsa:{{keylen}} -sha256" +  \
    " -nodes -keyout {{ outpath }}/example.com.key -out {{ outpath }}/example.com.crt -subj '{{dn}}'" + \
    " -addext '{{sans}}' -addext 'extendedKeyUsage=clientAuth'"
  # ppp = passphrase parameter
  # Avoid passphrase/key encryption. Varies between openssl 1.1.1 vs 3.x.y
  preq["ppp"] = "noenc" if p["ver"] == 3 else "nodes"
  preq["sans"] = form_san(p);
  preq["dn"]   = form_dn(p);
  template_r = jinja2.Template(reqtmpl)
  out = template_r.render(**preq)
  print("To create Run: "+out)
  print("To verify Run: "+"openssl x509 -in /tmp/cert.pem -text -noout")
