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



def asset(rfam, response):
  response.setJSON()

  # Extract the path, key and value...
  path = response.getPath()
  path = path[2:]
  path[-1] += '.json'
  
  key   = response.getQuery()['key']
  value = saxutils.unescape(response.getQuery()['value'])

  # Verify the inputs are sane...
  db = rfam.proj(response.project)
  try:
    node = db[path]
  except KeyError:
    response.make418()
    return
  
  if key not in ['name', 'description', 'owner', 'type', 'state', 'priority', 'render', 'final', 'support', 'rating']:
    response.make418()
    return
    
  if key=='owner' and value!='' and value not in rfam.getUsersByProject(response.project):
    response.make418()
    return
  if key=='owner' and value=='':
    value = None
    
  if key=='priority':
    value = int(value)
    
    priorities = rfam.proj_defaults(response.project)['priority.json'].read()
    if value < priorities['low'] or value > priorities['high']:
      response.append('false')
      return
  
  if key=='type' and value not in rfam.types(response.project):
    response.make418()
    return
  
  if key in ['render', 'final', 'support']:
    if value=='true':
      value = True
    elif value=='false':
      value = False
    else:
      response.make418()
      return
  
  if key=='support':
    if 'user' not in response.getQuery():
      response.make418()
      return
      
    user = saxutils.unescape(response.getQuery()['user'])
    if user not in rfam.getUsersByProject(response.project):
      response.make418()
      return
  
  # Do the update...
  if key=='support':
    meta = node.read()
    s = set(meta['support'])
    if value: s.add(user)
    else: s.discard(user)
    meta['support'] = list(s)
    node.write(meta)
    rfam.log(response, 'store_asset_support(%s,%s,%s)' % ('/'.join(path), user, str(value)))

  else: # Everything normal
    meta = node.read()
    meta[key] = value
    node.write(meta)
    rfam.log(response, 'store_asset(%s,%s,%s)' % ('/'.join(path), key, str(value)))

  response.append('true')



def job(rfam, response):
  response.setJSON()
  
  # Extract the uuid, key and value...
  uuid  = response.getPath()[2]
  key   = response.getQuery()['key']
  value = saxutils.unescape(response.getQuery()['value'])
  
  # Verify the request is sane...
  if not rfam.jobs.exists(uuid):
    response.make418()
    return
  
  if key not in ['priority', 'pause']:
    response.make418()
    return
    
  if key=='priority':
    value = int(value)
    
    priorities = rfam.proj_defaults(response.project)['priority.json'].read()
    if value < priorities['low'] or value > priorities['high']:
      response.append('false')
      return
  
  if key=='pause':
    value = (value=='true')
  
  # Do the update...
  if key=='priority':
    rfam.jobs.job_priority(uuid, value)
  elif key=='pause':
    rfam.jobs.job_pause(uuid, value)
  
  rfam.log(response, 'store_job(%s,%s,%s)' % (uuid, key, str(value)))
  response.append('true')



def node(rfam, response):
  response.setJSON()
  
  # Extract the ident, key and value...
  ident  = response.getPath()[2]
  key   = response.getQuery()['key']
  value = saxutils.unescape(response.getQuery()['value'])
  
  # Verify the request is sane...
  if not rfam.jobs.node_exists(ident):
    response.make418()
    return
  
  if key not in ['pause']:
    response.make418()
    return
  
  if key=='pause':
    value = (value=='true')

  # Do the update...
  if key=='pause':
    rfam.jobs.node_pause(ident, value)
  
  rfam.log(response, 'store_node(%s,%s,%s)' % (ident, key, str(value)))
  response.append('true')



def project(rfam, response):
  response.setJSON()
  
  # Extract the key and value...
  if 'key' not in response.getQuery():
    response.make418()
    return
    
  if 'value' not in response.getQuery():
    response.make418()
    return
  
  key   = response.getQuery()['key']
  value = saxutils.unescape(response.getQuery()['value'])
  
  # Handle the various supported keys...
  proj = rfam.proj(response.project)['project.json']
  
  if key in ['title', 'description', 'license']:
    p = proj.read()
    p[key] = value
    proj.write(p)
    
  elif key=='default':
    rfam.set_proj_defaults(response.project, value)

  else:
    response.make418()
    return
    
  # Report success...
  rfam.log(response, 'store_project(%s,%s)' % (key, str(value)))
  response.append('true')

  
  
def role(rfam, response):
  response.setJSON()

  # Extract the uuid, key and value...
  path = response.getPath()
  if len(path) < 3:
    response.make418()
    return
  
  ident = path[2]

  if 'key' not in response.getQuery():
    response.make418()
    return

  key = response.getQuery()['key']
  if key not in ['role', 'user', 'up', 'down']:
    response.make418()
    return
    
  move = key in ['up', 'down']

  if not move:
    if 'value' not in response.getQuery():
      response.make418()
      return
      
    value = saxutils.unescape(response.getQuery()['value'])
  
  if key=='user' and value not in rfam.getUsersByProject(response.project):
    response.make418()
    return
  
  # Perform the request with some further error checking...
  proj = rfam.proj(response.project)['project.json']
  if move:
    p = proj.read()
    
    if ident not in p['roles']:
      response.append('false')
      return
    
    order = list(map(lambda p: p[0], sorted(p['roles'].items(), key = lambda p: p[1]['order'])))
    pos = order.index(ident)
    
    if key=='up':
      if pos!=0:
        temp = p['roles'][ident]['order']
        p['roles'][ident]['order'] = p['roles'][order[pos-1]]['order']
        p['roles'][order[pos-1]]['order'] = temp
    else: # Down
      if (pos+1)!=len(order):
        temp = p['roles'][ident]['order']
        p['roles'][ident]['order'] = p['roles'][order[pos+1]]['order']
        p['roles'][order[pos+1]]['order'] = temp
    
    proj.write(p)
  else:
    p = proj.read()
  
    if ident not in p['roles']:
      response.append('false')
      return
  
    p['roles'][ident][key] = value
    proj.write(p)
  
  # Apply the request and return success...
  if not move:
    rfam.log(response, 'store_role(%s,%s,%s)' % (ident, key, str(value)))
  else:
    rfam.log(response, 'move_role(%s,%s)' % (ident, key))

  response.append('true')



def ext_asset(rfam, response):
  response.setJSON()
  
  # Extract the uuid, key and value...
  path = response.getPath()
  if len(path) < 3:
    response.make418()
    return
  
  if 'key' not in response.getQuery():
    response.make418()
    return
    
  if 'value' not in response.getQuery():
    response.make418()
    return
  
  ident = path[2]
  key   = response.getQuery()['key']
  value = saxutils.unescape(response.getQuery()['value'])
  
  if key not in ['description', 'license', 'origin']:
    response.make418()
    return
  
  # Perform the request with some further error checking...
  proj = rfam.proj(response.project)['project.json']
  p = proj.read()
  
  if ident not in p['ext_assets']:
    response.append('false')
    return
  
  p['ext_assets'][ident][key] = value
  proj.write(p)
  
  # Apply the request and return success...
  rfam.log(response, 'store_external_asset(%s,%s,%s)' % (ident, key, str(value)))
  response.append('true')



def app(rfam, response):
  # If the user is not logged in 404...
  if response.user==None or response.project==None:
    response.make404()
    return
  
  # Get the path - the first term decides which handler we are going to use...
  path = response.getPath()
  if len(path)<2:
    response.make418()
    return
  
  # Use the relevant handler...
  if path[1]=='asset':
    asset(rfam, response)
  elif path[1]=='job':
    job(rfam, response)
  elif path[1]=='node':
    node(rfam, response)
  elif path[1]=='project':
    project(rfam, response)
  elif path[1]=='role':
    role(rfam, response)
  elif path[1]=='ext_asset':
    ext_asset(rfam, response)
  elif path[1]=='emergency':
    emergency(rfam, response)
  else:
    response.make418()
