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



def role(rfam, response):
  response.setJSON()
  
  # Extract the details...
  if 'ident' not in response.getQuery():
    response.make418()
    return
  
  ident = response.getQuery()['ident']
  
  # Terminate the new role entry...
  proj = rfam.proj(response.project)['project.json']
  p = proj.read()
  if ident in p['roles']:
    rfam.log(response, 'remove_role(%s,%s)' % (p['roles'][ident]['role'], p['roles'][ident]['user']))
    
    del p['roles'][ident]
    proj.write(p)
    response.append('true')
    
  else:
    response.append('false')



def job(rfam, response):
  response.setJSON()

  # Get the uuid...
  path = response.getPath()
  if len(path)<3:
    response.make418()
    return
  
  uuid = path[2]
  
  # Remove it...
  if rfam.jobs.exists(uuid):
    rfam.log(response, 'remove_job(%s)' % uuid)
    
    rfam.jobs.remove(uuid)
    response.append('true')
    
  else:
    response.append('false')
  
  

def ext_asset(rfam, response):
  response.setJSON()
  
  # Extract the details...
  if 'ident' not in response.getQuery():
    response.make418()
    return
  
  ident = response.getQuery()['ident']
  
  # Terminate the new role entry...
  proj = rfam.proj(response.project)['project.json']
  p = proj.read()
  if ident in p['ext_assets']:
    rfam.log(response, 'remove_external_asset(%s)' % ident)
    
    del p['ext_assets'][ident]
    proj.write(p)
    response.append('true')
    
  else:
    response.append('false')



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
  if path[1]=='role':
    role(rfam, response)
  elif path[1]=='job':
    job(rfam, response)
  elif path[1]=='ext_asset':
    ext_asset(rfam, response)
  else:
    response.make418()
