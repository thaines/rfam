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
from collections import defaultdict

from .login import app as login



def app(rfam, response):
  # If the user is not logged in show them the login page...
  if response.user==None or response.project==None:
    login(rfam, response)
    return
  
  # Prepare the job list (At the same time record the work information for the nodes list)...
  work = dict()
  
  now = time.time()
  too_old = now - rfam.jobs.timeout
  
  tasks = defaultdict(lambda: defaultdict(list)) # Cache of which node is working on which task
  jobs = []
  job_list = [job for job in rfam.jobs.iterjobs()]
  job_list.sort(key=lambda job: job['project'] + job['name'])
  
  for job in job_list:
    # Clean up any expired working jobs...
    def keep_task(task):
      # Actual test, with structure update...
      if task[2]<too_old:
        if job['video']:
          job['todo'] = [i for i in range(task[0][0], task[0][1]+1)]
        else:
          if rfam.jobs.retry:
            job['todo'].append(task[0])
          else:
            job['failed'].append(task[0])
        job['errors'] += 1
        return False
      
      else:
        # This is somewhat abusive - record an index from node to task whilst filtering...
        tasks[task[1]][job['name']].append(task[0])
        
        return True
    
    job['working'] = [task for task in job['working'] if keep_task(task)]
    
    project = rfam.getProject(job['project'])['name']
    
    # Extract numbers for job...
    todo = len(job['todo'])
    done = len(job['done'])
    
    if job['video'] and len(job['working'])!=0:
      working = job['working'][0][0][1] + 1 - job['working'][0][0][0] - done
    else:
      working = len(job['working'])
    
    total = todo + working + done
    if total>0:
      percent = 100.0 * done / float(total)
    else:
      percent = 100.0
    
    if job['video']:
      mft = 'V'
    elif job['time_count']==0:
      mft = '?'
    else:
      mft = '%.1fs' % job['time']
    
    # Generate the interface elements...
    priority = rfam.priorityInterface(response.project, job['priority'])
    if done==total:
      control = rfam.template('jobs.control.done', {}, response)
    else:
      if job['pause']:
        control = rfam.template('jobs.control.paused', {}, response)
      else:
        control = rfam.template('jobs.control.working', {}, response)
    
    payload = {'uuid' : job['uuid'], 'project' : project, 'name' : job['name'], 'errors' : str(job['errors']), 'mft' : mft, 'todo' : todo, 'working' : working, 'done' : done, 'total' : total, 'percent' : percent, 'priority' : priority, 'control' : control}
    
    # Generate the row...
    html = rfam.template('jobs.row', payload, response)
    jobs.append(html)
  
  # Prepare the node list...
  nodes = []
  
  for node in rfam.jobs.iternodes():
    name = node['ident']
    if 'version' in node and node['version']!=None:
      name += ' (%s)' % node['version']
    if node['seen'] < too_old:
      name += rfam.getLanguage(response.user)['nodes:overdue']
    
    node_tasks = [name + ': ' + str(frames) for name, frames in tasks[node['ident']].items()]
    
    if node['paused']:
      control = rfam.template('nodes.control.paused', {}, response)
    else:
      control = rfam.template('nodes.control.working', {}, response)
    
    payload = {'ident' : node['ident'], 'name' : name, 'tasks' : ', '.join(node_tasks), 'pause' : control}
    
    html = rfam.template('nodes.row', payload, response)
    nodes.append(html)
  
  # Show the rendering page...
  head = '<link rel="stylesheet" href="/stylesheets/rendering.css"/>\n<script src="/javascript/rendering.js"></script>'
  payload = {'title' : rfam.getLanguage(response.user)['rendering'], 'head' : head, 'jobs' : '\n'.join(jobs), 'nodes' : '\n'.join(nodes), 'job_count' : len(jobs), 'node_count' : len(nodes)}
  html = rfam.template('rendering', payload, response)
  response.append(html)
  response.setHTML()
