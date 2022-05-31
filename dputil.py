# Data Processing utilities (read and parse files, setup templating,
# execute facilitating system commands ...)
# (c) Olli Hollmen
# License: MIT
import json
import sys
import os
import jinja2
import re
import subprocess
import yaml

ver = "0.92"

# TODO: Create higher level wrapping object for CL execution
# (cmd, ret code, results in stdout, stderr).
# Both stdout and stderr are stored in returned dict.
def run(cmd, **kwargs):
  ret = {"rc": -10000, "out": None, "err": None}
  cmdarr = cmd_arr(cmd)
  # Be slightly wasteful and store BOTH stdout and stderr for later
  # inspection (by caller). Seems text=... param not supported by older
  # version
  call = subprocess.run(cmdarr,
    stdout=subprocess.PIPE, stderr=subprocess.PIPE,  ) # text=True,
  ret["rc"]  = call.returncode
  ret["out"] = str(call.stdout)
  ret["err"] = str(call.stderr)
  if ret["rc"] and kwargs["onerror"]:
    # Check 
    kwargs["onerror"]("run: Error From command: "+cmd)
  return ret

# dputil.cmd_arr(cmdstr)
# Chunk a simple string version command to be split to POSIX exec() style
# array of CL arguments to be used with python (exec-style) subprocess.run().
# Note: Implementation is naive and assumes every CL option NOT contain
# whitespace chars
def cmd_arr(cmdline):
  return re.split(r'\s+', cmdline);

# dputil.tmpl_load(fn)
# Load and instantiate Jinja 2 template from a file.
# 
