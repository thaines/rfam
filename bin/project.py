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



def app(rfam, response):
  # If the user is not logged in show them the login page...
  if response.user==None or response.project==None:
    login(rfam, response)
    return
  
  # Access the project...
  db = rfam.proj(response.project)
  
  if 'project.json' in db:
    p = db['project.json'].read()
  else:
    p = None
    
  if p==None:
    p = {'title' : rfam.getLanguage(response.user)['default_title'], 'description' : '', 'roles' : {}, 'ext_assets' : {}, 'license' : rfam.getLanguage(response.user)['default_license'], 'default' : rfam.getDefault()}
    db.get_root().new('project.json', p)
    
  # Prepare the defaults part of the page...
  choice_default = rfam.defaultChoice(p['default'])
  
  # Prepare the add roles part of the page...
  choice_people = rfam.userChoice(response.project)
  
  # Prepare the roles part of the page...
  roles = []
  
  for key, value in sorted(p['roles'].items(), key = lambda p: p[1]['order']):
    user_choice = rfam.userChoice(response.project, value['user'])
    payload = {'ident' : key, 'role' : saxutils.escape(value['role']), 'user' : user_choice}
    roles.append(rfam.template('role', payload, response))
  
  roles = '\n'.join(roles)
  
  # Prepare the external assets part of the page...
  assets = []
  
  for key, value in sorted(p['ext_assets'].items(), key=lambda p: p[1]['description']):
    payload = {'ident' : key, 'description' : saxutils.escape(value['description']), 'license' : saxutils.escape(value['license']), 'origin' : saxutils.escape(value['origin'])}
    assets.append(rfam.template('asset.ext', payload, response))
  
  assets = '\n'.join(assets)
  
  # Prepare the automatic credits button...
  credits_button = rfam.template('button.credits', {}, response)
  
  # Show the project page...
  head = '<link rel="stylesheet" href="/stylesheets/project.css"/>\n<script src="/javascript/project.js"></script>'
  payload = {'title' : rfam.getLanguage(response.user)['project'], 'head' : head, 'project_title' : saxutils.escape(p['title']), 'project_description' : saxutils.escape(p['description']), 'project_license' : saxutils.escape(p['license']), 'roles' : roles, 'choice_people' : choice_people, 'ext_assets' : assets, 'choice_default' : choice_default, 'header_extra' : credits_button}
  html = rfam.template('project', payload, response)
  
  response.append(html)
  response.setHTML()
