#! /usr/bin/env python3
# Copyright 2015 Tom SF Haines

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time
import datetime
import json

import subprocess
from urllib.request import urlopen
import traceback



# Load the configuration...
f = open('config.json', 'r')
config = json.loads(f.read())
f.close()



# Its a simple loop...
while True:
  # Send request to server...
  try:
    req = urlopen('%s/potential'%config['server'], json.dumps(config['name']).encode('utf-8'))
    
  except IOError:
    # Problem - sleep a while and try again...
    print('Error talking to server:-(')
    time.sleep(config['retry_time'])
    continue
  
  # Turn response into a data structure...
  jobs = json.loads(req.read().decode('utf-8'))
  
  # Summarise response and print, counting how many jobs need to run on the cluster at the same time...
  print(datetime.datetime.utcnow().isoformat(' '), '::')
  total = 0
  for job in jobs:
    print('    %(name)s: fn=%(file)s priority=%(priority)i video=%(video)s requires=%(requires)s frames=%(frames)i' % job)
    
    run = True
    for req in job['requires']:
      if req not in config['provides']:
        run = False
        break
    
    if run:
      if job['video']:
        total += 1
        
      else:
        total += job['frames']
  
  print('  Counted %i jobs to be issued to cluster.' % total)
  
  # If the job count is not zero issue the command (there should be a drumroll here)...
  if total!=0:
    try:
      subprocess.call(config['cmd'] % total, shell=True)
    
    except:
      print(traceback.format_exc())
  
  # <stranger>Sleep now</stranger>...
  time.sleep(config['check_time'])
