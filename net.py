# Misc Network Operations
# 
def get_ip_address(serv):
  sl = serv.split(":") # "8.8.8.8"
  sl[1] = int(sl[1]) # Port To int
  
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  # From config
  s.connect(tuple(sl)) # ("8.8.8.8", 80)
  return s.getsockname()[0]
