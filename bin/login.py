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
from xml.sax.saxutils import quoteattr



def app(rfam, response):
  # If the call is to the login usr then do the login, otherwise ignore the url and just show the login page...
  path = response.getPath()
  if len(path)!=0 and path[0]=='login':
    # Check if the correct parameters have been provided...
    query = response.getQuery()
    project = query['project'] if 'project' in query else None
    user = query['user'] if 'user' in query else None
    if project==None or user==None:
      response.make403()
      return
    
    # Set the cookie via headers...
    response.addCookie('project', project, 24 if project!='' else -1)
    response.addCookie('user', user, 24 if user!='' else -1)
    
    # Return an empty json object...
    response.setJSON()
    response.append('{}')
    return
  
  # Setup the projects...
  projects = []
  
  for project in sorted(map(rfam.getProject, rfam.getProjects()), key=lambda p: p['name']):
    payload = {'ident' : project['ident'], 'name' : project['name']}
    html = rfam.template('login.project', payload, response)
    projects.append(html)
  
  projects = '\n'.join(projects)
  
  
  # Setup the users...
  users = []
  
  for user in sorted(map(rfam.getUser, rfam.getUsers()), key=lambda u: u['name']):
    projects_json = quoteattr(json.dumps(user['projects']))
    payload = {'ident' : user['ident'], 'name' : user['name'], 'projects' : projects_json}
    html = rfam.template('login.user', payload, response)
    users.append(html)
  
  users = '\n'.join(users)
  
  
  # Drop the projects and users into the final template...
  head = '<link rel="stylesheet" href="/stylesheets/login.css"/>\n<script src="/javascript/login.js"></script>'
  payload = {'title' : rfam.getLanguage()['login'], 'projects' : projects, 'users' : users, 'head' : head}
  html = rfam.template('login', payload, response)
  response.append(html)
  response.setHTML()
