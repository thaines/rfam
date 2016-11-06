# Copyright 2014 Tom SF Haines

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
import json



def app(rfam, response):
  # We are expecting a post of json, containing a list - get and verify...
  requests = response.getJsonPost()
  
  if not isinstance(requests, list):
    response.make418()
    return
  
  
  # Loop and process each part of the request in turn, building up the list of commandments to return...
  commandments = []
  name = None
  node_state = None
  
  
  for request in requests:
    rid = request['id']
    if rid=='identity':
      name = request['name']
      rfam.jobs.report(name, request['provides'], request['version'] if 'version' in request else None)
      
    elif rid=='info':
      # Default parameters...
      heartbeat = float(rfam.config['heartbeat'])
      hibernation = float(rfam.config['hibernation'])
      
      # Count number of nodes that are saying hi and adjust heartbeat accordingly using the rate_control parameter...
      count = 0
      too_old = time.time() - rfam.jobs.timeout
      for node in rfam.jobs.iternodes():
        if node['seen'] < too_old:
          continue
        count += 1
      
      rah = count / float(rfam.config['rate_control'])
      if heartbeat < rah:
        heartbeat = rah
      if heartbeat > hibernation:
        heartbeat = hibernation
      
      # Actual return...
      commandments.append({'id' : 'info', 'heartbeat' : heartbeat, 'arrhythmia' : float(rfam.config['arrhythmia']), 'error_scale' : float(rfam.config['error_scale']), 'hibernation' : hibernation, 'memory' : float(rfam.config['memory'])})
      
    elif rid=='task':
      if node_state==None and name!=None:
        root = rfam.jobs.nodes.get_root()
        node_state = root[name + '.json'].read()
      
      if node_state==None or node_state['paused']==False:
        for _ in range(request['count']):
          job = rfam.jobs.task_select(name, request['paths'], request['provides'])
          if job==None:
            break

          job['id'] = 'task'
          commandments.append(job)
    
    elif rid=='report':
      if not rfam.jobs.task_alive(name, request['uuid'], request['frame'], request['done'], request['total']):
        commandments.append({'id' : 'kill', 'uuid' : request['uuid'], 'frame' : request['frame']})
    
    elif rid=='done':
      rfam.jobs.task_done(request['uuid'], request['frame'], request['time'])
    
    else: # Unrecognised - error.
      response.make418()
      return
  
  # Convert the list fo commandments into a json return...
  response.setJSON()
  response.append(json.dumps(commandments))
