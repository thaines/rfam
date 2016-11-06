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

import os.path
import xml.sax.saxutils as saxutils



def app(rfam, response):
  # Verify the user is logged in...
  if response.user==None or response.project==None:
    response.make403()
    return
  
  # Work out which directory the user is requesting, and if we should be filtering out files not marked for rendering...
  path = response.getPath()[1:]
  show_all = response.getQuery()['show_all']=='true'
  inc_tail = response.getQuery()['inc_tail']=='true'
  
  # Basic prep...
  response.setHTML()
  old = rfam.getLanguage(response.user)['old']
  db = rfam.proj(response.project)
  
  # Add the header containing the current path...
  user_path = [rfam.getLanguage(response.user)['root']] + path
  parts = []
  
  for i, name in enumerate(user_path[:-1]):
    p = saxutils.escape('/'.join(path[:i])) if i>0 else ''
    parts.append(rfam.template('selector.part', {'name' : name, 'path' : p}, response))
  
  p = saxutils.escape('/'.join(path)) if len(path)>0 else ''
  parts.append(rfam.template('selector.last_part', {'name' : user_path[-1], 'path' : p}, response))
  
  html = rfam.template('selector.head', {'parts' : '/'.join(parts)}, response)
  response.append(html)
  
  # Generate html for the contents of that directory and feed it to the user...
  if path not in db:
    response.make404()
    return
  parent = db[path]
  
  if show_all:
    for part in parent:
      if part==old: continue # Skip depreciated versions of files.
      node = parent[part]
      if node.isa()==node.DIRECTORY:
        payload = {'path' : saxutils.escape('/'.join(path + [part])), 'name' : part}
        html = rfam.template('selector.directory', payload, response)
        response.append(html)
      
      if node.isa()==node.FILE and part.endswith('.blend'):
        payload = {'path' : saxutils.escape('/'.join(path + [part])), 'name' : part}
        html = rfam.template('selector.file', payload, response)
        response.append(html)
  
  else:
    for part in parent:
      if part==old: continue # Skip depreciated versions of files.
      node = parent[part]
      if node.isa()==node.DIRECTORY:
        payload = {'path' : saxutils.escape('/'.join(path + [part])), 'name' : part}
        html = rfam.template('selector.directory', payload, response)
        response.append(html)
      
      if node.isa()==node.FILE and part.endswith('.json'):
        meta = node.read()
        if meta!=None and 'type' in meta and 'owner' in meta and 'render' in meta and meta['render']:
          payload = {'path' : saxutils.escape('/'.join(path + [part[:-5]])), 'name' : part[:-5]}
          html = rfam.template('selector.file', payload, response)
          response.append(html)
  
  # If requested add a tail...
  if inc_tail:
    sall = 'checked' if show_all else ''
    html = rfam.template('selector.tail', {'show_all' : sall}, response)
    response.append(html)
