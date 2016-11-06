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



def true_priority(rfam, project, node, db = None, settings = None):
  """Given the node for a json asset file this returns its priority, taking into account the relevant project settings."""
  if settings==None:
    settings = rfam.proj_defaults(project)['priority.json'].read()
  
  meta = node.read()
  ret = meta['priority']
  state = rfam.getState(project, meta['state'])
  
  if settings['boosting'] and state['boost']:
    if db==None:
      db = rfam.proj(project)
      
    for child in meta['dependencies']:
      path = child.split('/')
      path[-1] += '.json'
      n = db[path]
      
      p = priority(rfam, project, n, db, settings)
      p += settings['boost']
      
      if p>ret:
        ret = p
  
  return ret



def user_task_list(rfam, user, project):
  """Given a user (ident), a project (ident) and the rfam object this returns a list of fs_db nodes, in order from highest priority to lowest priority. The Node-s are for the .json objects rather than the actual files, as that is what is typically required in the first instance."""
  
  # First build a list of assets that are owned by the user...
  ret = []
  
  db = rfam.proj(project)
  old = rfam.getLanguage()['old']
  
  for path in db:
    if old in path: continue # Skip depreciated versions of files.
    node = db[path]
    if node.isa()==node.FILE and path[-1].endswith('.json'):
      meta = node.read()
      if meta!=None and 'type' in meta and 'owner' in meta and meta['owner']==user:
        ret.append(node)
  
  # Sort and return...
  settings = rfam.proj_defaults(project)['priority.json'].read()
  ret.sort(key = lambda node: -true_priority(rfam, project, node, db, settings))
  return ret



def project_tasks(rfam, project):
  """Returns a dictionary indexed by user identifier giving the json Node of their highest priority task - basically a list of everything that is currently being worked on."""
  ret = dict()
  
  db = rfam.proj(project)
  settings = rfam.proj_defaults(project)['priority.json'].read()
  old = rfam.getLanguage()['old']
  
  for path in db:
    if old in path: continue # Skip depreciated versions of files.
    node = db[path]
    if node.isa()==node.FILE and path[-1].endswith('.json'):
      meta = node.read()
      if meta!=None and 'type' in meta and 'owner' in meta and meta['owner']!=None:
        p = true_priority(rfam, project, node, db, settings)
        if meta['owner'] not in ret or ret[meta['owner']][0]<p:
          ret[meta['owner']] = (p, node)
  
  for key in ret.keys():
    ret[key] = ret[key][1]
  
  return ret
