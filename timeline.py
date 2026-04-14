#!/usr/bin/env python3
# ## Module to log events and tasks in time
# - Event - a point in time (with no no duration or particular start and end times)
# - Span/Task - Timespan with start moment and end moment and respective duration.
#   - Added by calls to start() and end() to signal start and end respectively.
# Add all times as UNIX epoc time, which is easy to operate on (to calculate)
import json
import time
# import datetime # datetime.datetime.fromtimestamp(1735689600, tz=timezone.utc)
def ts():
  # time.time() defaults to float !
  #return time.time() # float !
  # return int(time.time()) # Full seconds (int) ?
  return time.time_ns() / 1000000 # Nano secs => millis

# ts from datetime
#now = datetime.datetime.now()
#epoch_now = now.timestamp()

def timeline_new(name):
  # TODO: Timezone (delta from UTC) ? Or keep everyting as UTC ?
  # TODO: Resolution seconds, millis ?
  return {"name": name, "line": [], "idx": {}}

def add(tl, evlbl):
  ev = {"lbl": evlbl, "ts": ts()}
  tl["line"].append(ev)
  tl["idx"][evlbl] = ev

def start(tl, evlbl):
  s0 = {"lbl": evlbl, "span": [ts()]}
  tl["line"].append(s0)
  tl["idx"][evlbl] = s0
def end(tl, evlbl):
  s = tl["idx"][evlbl]
  if not s: print(f"Task span labeled '{evlbl}' has not started !!!"); return
  if len(s["span"]) != 1:
    print(f"Task '{evlbl}' neneds to start and cannot end multiple times")
    return
  s["span"].append(ts())

if __name__ == "__main__":
  # TODO (example): birth, babtizing, walktime, cranky-age(st,end)
  tl = timeline_new("Test timeline")
  add(tl, "ev1")
  start(tl, "job1")
  time.sleep(1)
  end(tl, "job1")
  #print(tl)
  print(json.dumps(tl, indent=2))
