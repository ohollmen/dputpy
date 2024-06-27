# Ansible PB related functionality
# - Extracting tasks from playbooks fro checks
# - Exploding PB:s to roles or Gathering roles to playbooks
# - Creating emty-valued stub parameter files (JSON or YAML) out of PB 'vars:' sections or var files 
# - Possibly collecting documentation out of (flat) parameter/variable YAML files
# Initially limit the number of module types supported to most essential crucial ones
import sys # argv
import yaml
import json

modtypes = {
  "lineinfile": {},
  "template": {},
  
}
# lifp - lineinfile params - w. focus on path,line,state,regexp (and absence of reg
#  Expects lifp to be extrached before
def lineinfile_test(lifp):
  if lifp.get("state") == "absent":
    pass
  # "present" or state missing
  else:
    pass
  # Load File by "path" (treat as lines)
  # Match regexp
  
  return 1

# Get a task from YAML by mod-type, by name pattern
def task_get(arr, nmappt):
  return 1

# Recognize a few select module types by their keys on the top level of task
# TODO: Should get both type and params for better / fast processing ? Or sep method
def task_mod_type(t): # t = Task
  # test if there is a member w. dot-notation, return basename
  def hasdotnot(t):
    for k in t.keys():
      if k.find('.') > 1:
        l = k.split('.')
        #print("Found DOT-NOT "+k);
        return l[-1]
    return None
  m = hasdotnot(t)
  if m: return m
  if t.get("lineinfile")  or t.get("ansible.builtin.lineinfile"): return "lineinfile"
  if t.get("blockinfile") or t.get("ansible.builtin.blockinfile"): return "blockinfile"
  if t.get("file")    or t.get("ansible.builtin.file"): return "file"
  if t.get("shell")   or t.get("ansible.builtin.shell"): return "shell"
  if t.get("copy")    or t.get("ansible.builtin.copy"): return "copy"
  if t.get("replace") or t.get("ansible.builtin.replace"): return "replace"
  # Check absent
  if t.get("yum")     or t.get("ansible.builtin.yum"): return "yum"
  if t.get("user")    or t.get("ansible.builtin.user"): return "user"
  # 06-24
  if t.get("apt")    or t.get("ansible.builtin.apt"): return "apt"
  if t.get("debug")    or t.get("ansible.builtin.debug"): return "debug"
  if t.get("systemd")    or t.get("ansible.builtin.systemd"): return "systemd"
  if t.get("package")    or t.get("ansible.builtin.package"): return "package"
  if t.get("setup")    or t.get("ansible.builtin.setup"): return "setup"
  if t.get("template")    or t.get("ansible.builtin.template"): return "template"
  if t.get("authorized_key")    or t.get("ansible.builtin.authorized_key"): return "authorized_key"
  # 
  if t.get("stat")    or t.get("ansible.builtin.stat"): return "stat"
  # set_fact
  if t.get("set_fact")    or t.get("ansible.builtin.set_fact"): return "set_fact"
  if t.get("command")    or t.get("ansible.builtin.command"): return "command"
  # Hmm, NOT a module: https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_delegation.html
  # if t.get("local_action")    or t.get("ansible.builtin.local_action"): return "local_action"
  return

def ispb(d):
  # Others: name, vars, become  and d.get("")
  if d.get("hosts") and d.get("tasks"): return 1
  return 0
def hastab(cont):
  ls = cont.split("\n");
  i = 1
  for l in ls:
    if '\t' in l: return i
    i += 1
  return 0
# Test if param state: absent is defined
# Todo look at module params (tricky - should get task_mod_type ?
def absent(tp):
  #
  abt = tp.get("absent")
  if abt:
    return 1 # In Yes,yes. test str/bool
  return 0

if __name__ == "__main__":
  fn = sys.argv[1]
  cont = None
  cfg = None
  try:
    cont = open(fn, "r").read()
    #print("Read ok");
    ln = hastab(cont)
    if ln: print("file "+fn+" has tabs (l. "+str(ln)+")"); exit(1)
    cfg = yaml.safe_load(cont)
    #print("Parsed ok");
  # except BaseException, e: https://stackoverflow.com/questions/442343/generic-catch-for-python
  except Exception as e:
    print("Error Reading or parsing file ("+fn+"): "+str(e)); exit(1);
  
  
  while isinstance(cfg, list) and (len(cfg) == 1): cfg = cfg[0]
  if not cfg: print("Could not find a root/start entity from file "+fn) # print(json.dumps())
  #cfg = cfg[0]
  #print("cfg is: "+str(type(cfg)));
  #print(json.dumps(cfg, indent=2))
  tasks = None
  if not isinstance(cfg, dict): print("Root is not a pb-dict (cannot access any members, is this a role-file ?) !!!");exit(1)
  #try:
  tasks = cfg.get("tasks")
  
  print("## Tasks of "+fn);
  for t in tasks:
    m = task_mod_type(t)
    #print("TaskMod: "+str(m))
    if not m: print(json.dumps(t))
