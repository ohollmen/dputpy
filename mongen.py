# Operations to generate/update monitoring related entities
# - Monitoring / Alert Profiles
# - Notification channels
# (c) Olli Hollmen
# License: MIT

# Allow setting config "into" module
cfg = None
# dputil.channel_gen(cfg)
# Create Notification channel
#
def channel_gen():
  
  tmplfn = cfg.get("tmpls").get("channel")
  outfn  = "/tmp/notify_channel.json"
  tmpl = tmpl_load(tmplfn);
  out = tmpl.render(**cfg)
  filewrite(out, outfn)
  cmdarr = cmd_arr(fnames["gcloud"]+" alpha monitoring channels create --channel-content-from-file "+outfn)
  
