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
from .misc import format_bytes



def app(rfam, response):
  # If the user is not logged in show them the login page...
  if response.user==None or response.project==None:
    login(rfam, response)
    return
  
  # Get the information for the requested asset...
  db = rfam.proj(response.project)
  json_path = response.getPath()[1:]
  path = '/'.join(json_path)
  json_path = json_path[:-1] + [json_path[-1] + '.json']
  asset = db[json_path].read()
  
  try:
    blend = db[response.getPath()[1:]]
  except KeyError:
    blend = None
  
  # Prepare the back/new buttons...
  new_button = rfam.template('button.back_new', {}, response)
  
  # Prepare assorted bits of information...
  type_choice = rfam.typeChoice(response.project, asset['type'])
  state = rfam.stateChoice(response.project, asset['type'], asset['state'])
  priority = rfam.priorityInterface(response.project, asset['priority'])
  render = 'checked' if asset['render'] else ''
  final = 'checked' if asset['final'] else ''
  
  owner = rfam.userChoice(response.project, asset['owner'], True)
  
  support = []
  
  for ident in rfam.getUsersByProject(response.project):
    user = rfam.getUser(ident)
    checked = 'checked' if ident in asset['support'] else ''
    support.append(rfam.template('asset.support', {'ident':ident, 'name' : saxutils.escape(user['name']), 'checked' : checked}, response))
  
  support = '\n'.join(support)
  
  render_stats = rfam.format_render_time(response.user, asset)
  
  modified = blend.modified().strftime(rfam.getLanguage(response.user)['asset:modified:format']) if blend!=None else rfam.getLanguage(response.user)['NA']
  size = format_bytes(blend.size()) if blend!=None else rfam.getLanguage(response.user)['NA']
  if asset['creator']!=None:
    creator = rfam.getUser(asset['creator'])['name']
  else:
    creator = rfam.getLanguage(response.user)['asset:unknown_user']
  
  if blend==None:
    path_extra = rfam.getLanguage(response.user)['not_found']
  else:
    path_extra = None
  
  # Show the asset page...
  head = '<link rel="stylesheet" href="/stylesheets/asset.css"/>\n<script src="/javascript/asset.js"></script>'
  payload = {'title' : response.getPath()[-1], 'header_extra' : new_button, 'head' : head, 'path' : path, 'path_extra' : path_extra, 'name' : asset['name'], 'description' : asset['description'], 'type' : type_choice, 'owner' : owner, 'support' : support, 'state' : state, 'priority' : priority, 'render' : render, 'final' : final, 'render_stats' : render_stats, 'modified' : modified, 'size' : size, 'creator' : creator}
  html = rfam.template('asset', payload, response)
  response.append(html)
  response.setHTML()
