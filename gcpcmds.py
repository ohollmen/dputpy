# Groups of GCP Commands (as templates)
# Keep as separate lists for ease of handling a grouped commands context.


tmpls_idx = {}
# Set project, VM stop, VM start, VM meta backup, dns change
# { "id": "", "title": "", "tmpl": ""},
tmpls_uni = [
  { "id": "proj_set", "title": "Set Project",
    "tmpl": "gcloud config set project {{ projid }}" },
  { "id":"vmi_stop", "title": "Stop VM instance",
  "tmpl": "gcloud compute instances stop {{ vmname_d }} --zone {{ zone_b }}" },
  { "id": "vmi_start", "title": "Start VM Instance",
  "tmpl":"gcloud compute instances start {{ vmname_d }}  --zone={{ zone_b }}" },
  
  { "id": "vmi_meta", "title": "Store VM Meta info",
    "tmpl": "gcloud compute instances describe --format json --zone {{ zone }} {{ hname }} > {{ hname }}.dr_backup.{{ isodate }}.json"},
  { "id": "dns_update", "title": "Update DNS record",
  "tmpl": "gcloud dns record-sets update {{ servdns }}.{{ domainname }} --rrdatas '{{ newip }}' --type {{ rectype }} " + \
     "--ttl={{ dnsttl }} --zone=projects/{{ projid }}/managedZones/{{ domainzone }} --project={{ projid }}" },
]

def init():
  # Index all sets ?
  
  return

def tmpl_get(id):
  return tmpls_idx.get(id)

# Run command expanded (to out), check if post-processing is needed
def run():
  #
  return

if __name__ == "__main__":
  print("Template ...");
