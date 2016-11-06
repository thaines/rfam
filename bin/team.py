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
  
  # Create the user panes...
  users = []
  index = 0
  
  user_idents = rfam.getUsersByProject(response.project)
  user_idents = [(ident, rfam.getUser(ident)) for ident in user_idents]
  user_idents.sort(key = lambda pair: pair[1]['name'])
  
  user_to_task = project_tasks(rfam, response.project)
  
  for ident, user in user_idents:
    side = 'box' if ((index%2)==0) else 'box_right'
    
    if ident in user_to_task:
      meta = user_to_task[ident].read()
      path = attr_escape('/'.join(user_to_task[ident].path())[:-5])
      
      payload = {'path' : path, 'name' : meta['name']}
      task = rfam.template('team.task', payload, response)
      
    else:
      task = rfam.getLanguage(response.user)['team:lazy']
    
    support = []
    if ident in user_to_task:
      for sui in meta['support']:
        su = rfam.getUser(sui)
        support.append('<div>%s</div>' % su['name'])
      
      if len(support)==0:
        support.append(rfam.getLanguage(response.user)['team:nobody'])
        
    else:
      support.append(rfam.getLanguage(response.user)['team:na'])
    
    payload = {'class' : side, 'ident' : ident, 'name' : user['name'], 'task' : task, 'support' : '\n'.join(support)}
    users.append(rfam.template('team.user', payload, response))
    
    index += 1
  
  # Show the team page...
  head = '<link rel="stylesheet" href="/stylesheets/team.css"/>\n<script src="/javascript/team.js"></script>'
  payload = {'title' : rfam.getLanguage(response.user)['team'], 'head' : head, 'users' : '\n'.join(users)}
  html = rfam.template('team', payload, response)
  response.append(html)
  response.setHTML()
