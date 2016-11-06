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

import json
import xml.sax.saxutils as saxutils

from .login import app as login
from .priority import *



def attr_escape(s):
  return saxutils.escape(s).replace('"',"&quot;")



def app(rfam, response):
  # If the user is not logged in show them the login page...
  if response.user==None or response.project==None:
    login(rfam, response)
    return
  
  # Get the assorted priority information...
  assists = project_tasks(rfam, response.project)
  jobs = user_task_list(rfam, response.user, response.project)
  
  # Setup all assets...
  current = []
  for user, json_node in assists.items():
    if user!=response.user:
      meta = json_node.read()
      if response.user in meta['support'] and meta['owner']!=None:
        owner = rfam.getUser(meta['owner'])
        path = attr_escape('/'.join(json_node.path())[:-5])
        asset_type = rfam.getType(response.project, meta['type'])['name']
        state = rfam.getState(response.project, meta['state'])['name']
        
        payload = {'ident' : meta['owner'], 'name' : owner['name'], 'asset' : meta['name'], 'path' : path, 'type' : asset_type, 'state' : state}
        current.append(rfam.template('home.assist', payload, response))
  
  # Do the first asset; if they don't have any indicate as such...
  if len(jobs)>0:
    meta = jobs[0].read()
    path = attr_escape('/'.join(jobs[0].path())[:-5])
    asset_type = rfam.getType(response.project, meta['type'])['name']
    owner = rfam.userChoice(response.project, meta['owner'], True)
    state = rfam.stateChoice(response.project, meta['type'], meta['state'])
    priority = rfam.priorityInterface(response.project, meta['priority'])
    
    support = []
    for sui in meta['support']:
      su = rfam.getUser(sui)
      payload = {'ident' : sui, 'name' : su['name']}
      support.append(rfam.template('home.asset.support', payload, response))
    support = '\n'.join(support)
    
    render_stats = rfam.format_render_time(response.user, meta)
    
    payload = {'name' : meta['name'], 'description' : meta['description'], 'path' : path, 'type' : asset_type, 'owner' : owner, 'state' : state, 'priority' : priority, 'support' : support, 'render_stats' : render_stats}
    current.append(rfam.template('home.asset', payload, response))
    
  else:
    current.append(rfam.getLanguage(response.user)['home:freedom'])
  
  # Do the remaining assets - code is the same as for the asset list...  
  if len(jobs)>1:
    # Fetch the correct header for the asset list...
    if rfam.proj_defaults(response.project)['priority.json'].read()['visible']:
      assets_head = rfam.template('assets.head_priority', {}, response)
      row_template = 'assets.row_priority'
    else:
      assets_head = rfam.template('assets.head', {}, response)
      row_template = 'assets.row'
  else:
    assets_head = ''
  
  ident = 0
  assets = []
  
  for job in jobs[1:]:
    path = job.path()
    meta = job.read()
    
    at = rfam.getType(response.project, meta['type'])
    at = at['name'] if at!=None else '? - error'
    owner = rfam.userChoice(response.project, meta['owner'], True)
    state = rfam.stateChoice(response.project, meta['type'], meta['state'])
    priority = rfam.priorityInterface(response.project, meta['priority'])
      
    payload = {'id' : str(ident), 'path' : attr_escape(('/'.join(path))[:-5]), 'name' : meta['name'], 'type' : at, 'owner' : owner, 'state' : state, 'priority' : priority, 'true_priority' : true_priority(rfam, response.project, job)}
    assets.append(rfam.template(row_template, payload, response))
      
    ident += 1
  
  # Show the home page...
  head = '<link rel="stylesheet" href="/stylesheets/assets.css"/>\n<script src="/javascript/assets.js"></script>\n<link rel="stylesheet" href="/stylesheets/home.css"/>\n<script src="/javascript/home.js"></script>'
  payload = {'title' : rfam.getLanguage(response.user)['home'], 'head' : head, 'current' : '\n'.join(current), 'assets_head' : assets_head, 'assets' : '\n'.join(assets)}
  html = rfam.template('home', payload, response)
  response.append(html)
  response.setHTML()
