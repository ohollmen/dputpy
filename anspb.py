# Ansible PB related functionality
# - Extracting tasks from playbooks fro checks
# - Exploding PB:s to roles or Gathering roles to playbooks
# - Creating emty-valued stub parameter files (JSON or YAML) out of PB 'vars:' sections or var files 
# - Possibly collecting documentation out of (flat) parameter/variable YAML files
# Initially limit the number of module types supported to most essential crucial ones

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
  if t.get("lineinfile")  or t.get("ansible.builtin.lineinfile"): return "lineinfile"
  if t.get("blockinfile") or t.get("ansible.builtin.blockinfile"): return "blockinfile"
  if t.get("file")    or t.get("ansible.builtin.file"): return "file"
  if t.get("shell")   or t.get("ansible.builtin.shell"): return "shell"
  if t.get("copy")    or t.get("ansible.builtin.copy"): return "copy"
  if t.get("replace") or t.get("ansible.builtin.replace"): return "replace"
  # Check absent
  if t.get("yum")     or t.get("ansible.builtin.yum"): return "yum"
  if t.get("user")    or t.get("ansible.builtin.user"): return "user"
  
  return

# Test if param state: absent is defined
# Todo look at module params (tricky - should get task_mod_type ?
def absent(tp):
  #
  return
