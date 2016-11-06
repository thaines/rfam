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

import datetime



def emergency(rfam, response):
  """Provides the ability to pause and unpause all rendering nodes."""
  op = response.getPath()[2]
  
  if op=='stop':
    rfam.jobs.node_pause_all(True)
    rfam.log(response, 'emergency_stop()')
  elif op=='start':
    rfam.jobs.node_pause_all(False)
    rfam.log(response, 'emergency_start()')
  else:
    response.make418()
    return

  response.setJSON()
  response.append('true')



def reset_stats(rfam, response):
  """Allows you to reset the rendering statistics of a file."""
  
  # Extract the path to the json file...
  path = response.getPath()
  path = path[2:]
  path[-1] += '.json'
  
  # Get the related node if it exists...
  db = rfam.proj(response.project)
  try:
    node = db[path]
  except KeyError:
    response.make418()
    return
  
  # Terminate render time information...
  meta = node.read()
  if 'render_time' in meta:
    del meta['render_time']
    node.write(meta)
    
  # Record success...
  rfam.log(response, 'reset_stats(%s)' % '/'.join(path))
  response.setJSON()
  response.append('true')



def checkpoint(rfam, response):
  """Checkpoints a file - makes a copy with a timestamp in its name, in a subdirectory"""
  
  # Extract the path to the blend file...
  path = response.getPath()
  path = path[2:]
  
  # Check it exists...
  db = rfam.proj(response.project)
  try:
    origin = db[path]
  except KeyError:
    response.make418()
    return
  
  # Copy it, adding a date and time to its filename...
  now = datetime.datetime.utcnow()
  dest_path = path[:-1] + [rfam.getLanguage()['old'], path[-1] + ' ' + now.isoformat(' ')]
  
  parent = db.get_root().create(dest_path[:-1])
  parent.clone(dest_path[-1], origin)
  
  # Record success...
  rfam.log(response, 'checkpoint(%s)' % '/'.join(path))
  response.setJSON()
  response.append('true')



def delete(rfam, response):
  """Deletes a filoe, by copying it to an ignore directory"""
  
  # Extract the paths to the blend and json files...
  path = response.getPath()
  path = path[2:]
  
  path_json = path[:]
  path_json[-1] += '.json'
  
  # Check the exists...
  db = rfam.proj(response.project)
  try:
    origin = db[path]
    origin_json = db[path_json]
  except KeyError:
    response.make418()
    return
  
  # Copy it, adding a date and time to its filename...
  now = datetime.datetime.utcnow()
  dest_path = path[:-1] + [rfam.getLanguage()['old'], path[-1] + ' ' + now.isoformat(' ')]
  dest_path_json = dest_path[:-1] + [path_json[-1] + ' ' + now.isoformat(' ')]
  
  parent = db.get_root().create(dest_path[:-1])
  parent.clone(dest_path[-1], origin)
  parent.clone(dest_path_json[-1], origin_json)
  
  # Terminate the original files...
  origin.remove()
  origin_json.remove()
  
  # Record success...
  rfam.log(response, 'delete(%s)' % '/'.join(path))
  response.setJSON()
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
  if path[1]=='emergency':
    emergency(rfam, response)
  elif path[1]=='reset_stats':
    reset_stats(rfam, response)
  elif path[1]=='checkpoint':
    checkpoint(rfam, response)
  elif path[1]=='delete':
    delete(rfam, response)
  else:
    response.make418()
