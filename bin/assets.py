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

import xml.sax.saxutils as saxutils

from .login import app as login
from .priority import true_priority



def attr_escape(s):
  return saxutils.escape(s).replace('"',"&quot;")



def app(rfam, response):
  # If the user is not logged in show them the login page...
  if response.user==None or response.project==None:
    login(rfam, response)
    return
  
  # Prepare the new button...
  new_button = rfam.template('button.new', {}, response)

  # Fetch the correct header for the asset list...
  if rfam.proj_defaults(response.project)['priority.json'].read()['visible']:
    assets_head = rfam.template('assets.head_priority', {}, response)
    row_template = 'assets.row_priority'
  else:
    assets_head = rfam.template('assets.head', {}, response)
    row_template = 'assets.row'
  
  # Generate the list of asset types...
  types = []
  
  for ident in rfam.types(response.project):
    at = rfam.getType(response.project, ident)
    
    payload = {'ident' : ident, 'name' : at['name']}
    types.append((rfam.template('assets.type', payload, response), at['sort']))
  
  types.sort(key=lambda t: t[1])
  types = '\n'.join(map (lambda t: t[0], types))
  
  # Generate the list of assets for the table...
  assets = []
  
  db = rfam.proj(response.project)
  old = rfam.getLanguage(response.user)['old']
  
  ident = 0
  for path in db:
    if old in path: continue # Skip depreciated versions of files.
    node = db[path]
    if node.isa()==node.FILE and path[-1].endswith('.json'):
      meta = node.read()
      if meta==None or ('type' not in meta) or ('owner' not in meta):
        continue
      
      at = rfam.getType(response.project, meta['type'])
      at = at['name'] if at!=None else '? - error'
      owner = rfam.userChoice(response.project, meta['owner'], True)
      state = rfam.stateChoice(response.project, meta['type'], meta['state'])
      priority = rfam.priorityInterface(response.project, meta['priority'])
      
      payload = {'id' : str(ident), 'path' : attr_escape(('/'.join(path))[:-5]), 'name' : meta['name'], 'type_ident' : meta['type'], 'type' : at, 'owner' : owner, 'state' : state, 'priority' : priority, 'true_priority' : true_priority(rfam, response.project, node)}
      assets.append(rfam.template(row_template, payload, response))
      
      ident += 1
  
  assets = '\n'.join(assets)
  
  # Show the assets page...
  head = '<link rel="stylesheet" href="/stylesheets/assets.css"/>\n<script src="/javascript/assets.js"></script>'
  payload = {'title' : rfam.getLanguage(response.user)['assets'], 'header_extra' : new_button, 'head' : head, 'types' : types, 'assets_head' : assets_head, 'assets' : assets, 'count' : str(ident)}
  html = rfam.template('assets', payload, response)
  response.append(html)
  response.setHTML()
