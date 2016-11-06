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

from .login import app as login



def app(rfam, response):
  # If the user is not logged in show them the login page...
  if response.user==None or response.project==None:
    login(rfam, response)
    return
  
  response.setPlain()
  db = rfam.proj(response.project)
  proj = db['project.json'].read()
  
  # Show a very basic text file, built from the project file - basically the credits, though without anything special going on, so the user is almost certainly going to want to edit them...
  
  ## First step - get a list of all users, so we can tick them off as they are added in...
  spare_users = set(rfam.getUsersByProject(response.project))
  
  ## Go through the roles list - do some checks for when a role is repeated so they can be merged...
  prev_role = None
  for role in sorted(proj['roles'].values(), key = lambda role: role['order']):
    if prev_role!=role['role']:
      if prev_role!=None:
        response.append('\n\n')
      response.append(role['role'])
      response.append('\n\n')
      prev_role = role['role']
    
    response.append(rfam.getUser(role['user'])['name'])
    response.append('\n')
    
    spare_users.discard(role['user'])
  
  ## Add all remaining users...
  if prev_role!=None and len(spare_users)!=0:
    response.append('\n\n')
  
  for user in sorted(spare_users):
    response.append(rfam.getUser(user)['name'])
    response.append('\n')
  
  ## Add in the external asset licenses...
  response.append('\n\n\n')
  for ext_asset in sorted(proj['ext_assets'].values(), key=lambda ext_asset: ext_asset['description']):
    response.append(ext_asset['description'])
    response.append('\n')
    response.append(ext_asset['license'])
    response.append('\n')
    response.append(ext_asset['origin'])
    response.append('\n\n\n')
  
  ## Add in the final licensing information...
  response.append('\n')
  response.append(proj['title'])
  response.append('\n')
  response.append(proj['license'])
  
  rfam.log(response, 'credits()')
