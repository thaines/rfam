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
import os.path
import uuid
import xml.sax.saxutils as saxutils

from .priority import true_priority
from .fs_db import *

from .prman_AlfParser import prman_AlfParser


def asset(rfam, response):
  response.setJSON()
  
  # Extract the details...
  if not {'name', 'type', 'filename', 'description'} <= set(response.getQuery().keys()):
    response.make418()
    return
  
  name = saxutils.unescape(response.getQuery()['name'])
  at = response.getQuery()['type']
  filename = saxutils.unescape(response.getQuery()['filename'])
  description = saxutils.unescape(response.getQuery()['description'])
  
  # Verify they are sane, and parse them a bit...
  at = rfam.getType(response.project, at)
  if at==None:
    response.make418()
    return
  
  filename = os.path.normpath(filename).split('/')
  for part in filename:
    if len(part)==0 or part[0]=='.' or '\\' in part or '?' in part or '*' in part:
      response.append('false')
      return
  
  db = rfam.proj(response.project)
  db.get_root().create(filename[:-1])
  container = db[filename[:-1]]
  if 'file' in at and (container.isa()!=Node.DIRECTORY or filename[-1] in container):
    # Already exists - cancel...
    response.append('false')
    return
  
  # Create the .blend file...
  if 'file' in at:
    ddb = rfam.proj_defaults(response.project)
    source = os.path.normpath('asset_types/' + at['file']).split('/')
    source = ddb[source]
  
    container.clone(filename[-1], source)
  
  # Create the .json file...
  meta = {'name' : name, 'description' : description, 'type' : at['ident'], 'creator' : response.user, 'owner' : None, 'support' : [], 'state' : at['state'], 'priority' : at['priority'], 'render' : at['render'], 'final' : at['final'], 'time_budget' : at['time_budget'], 'dependencies' : []}
  
  container.new(filename[-1] + '.json', meta)
  
  # Return succes...
  rfam.log(response, 'new_asset(%s,%s,%s,%s)' % (name, at['ident'], filename, description))
  response.append('true')


def job_prman(rfam, response):
  # Extract the request - path plus parameters...
  path  = response.getPath()[2:]
  name = response.getQuery()['name']

  # If this is not an alf file, return early
  if not name.endswith('.alf'):
    reponse.setJSON()
    response.append(json.dumps(['ERROR: Job must be a .alf file!']))
    return

  start = int(response.getQuery()['start'])
  end   = int(response.getQuery()['end'])
  final = response.getQuery()['final']=='true'
  
  # Verify the path exists...
  db = rfam.proj(response.project)
  if path not in db:
    response.setJSON()
    response.append(json.dumps(['ERROR: Path to file does not exist!']))
    return
  
  # Convert path into a proper filename...
  ps = rfam.getProject(response.project)
  fn = os.path.join(ps['directory'], *path)

  # Load and parse the alf file
  try:
    # Make the path compatible for windows and linux
    actualFilePath = rfam.real(fn)
    # Attempt to parse the .alf file
    parser = prman_AlfParser()
    with open(actualFilePath, 'r') as myfile:
          data = myfile.read()
    textureCommands, frameCommands, frameIdxs = parser.parseFile(data)
  except:
    response.setJSON()
    response.append(json.dumps(['ERROR: The .alf file could not be parsed!']))
    return

  # Make sure the frame range checks out!
  jobMinFrame = frameIdxs[0]
  jobMaxFrame = frameIdxs[-1]

  # Correct it if necessary
  start_corrected = max(start, jobMinFrame)
  end_corrected = min(end, jobMaxFrame)  

  # Make sure the result is still anything valid
  if start_corrected > end_corrected:
    response.setJSON()
    response.append(json.dumps(['ERROR: Given the actual number of jobs exported in the .alf file' \
    + ' [ ' + str(jobMinFrame) + ' - ' + str(jobMaxFrame) + ' ], the requested job' \
    + ' [ ' + str(start) + ' - ' + str(end_corrected) + ' ] is invalid!']))
    return

  # Make sure there are no pre-processing commands (alternatively process locally)
  if len(textureCommands) > 0:
    response.setJSON()
    response.append(json.dumps(['ERROR: The .alf job contains texture conversion commands which must be processed locally!']))

  # Calculate the jobs default priority...
  json_path = path[:]
  json_path[-1] += '.json'
  
  if json_path in db:
    priority = true_priority(rfam, response.project, db[json_path], db)
  else:
    settings = rfam.proj_defaults(response.project)['priority.json'].read()
    priority = settings['low']
  
  #create some json for commands
  prmanCommands = {'commands' : { 'texture' : textureCommands, 'frames' : frameCommands } }

  # Create the job...
  uuid = rfam.jobs.add(name, response.project, fn, start_corrected, end_corrected,
    priority, final, [], json_path, prmanCommands = prmanCommands)
  
  # Create a response string to inform the user of the actual frame range used
  responseString = 'You requested processing of frames [ ' + str(start) + ' - ' + str(end) + ' ].' \
  + ' Ribs were exported for frames [ ' + str(jobMinFrame) + ' - ' + str(jobMaxFrame) + ' ].' \
  + ' The system will render [ ' + str(start_corrected) + ' - ' + str(end_corrected) + ' ].'

  # Return success...
  rfam.log(response, 'new_job(%s,%s,%i,%i,%s)' % (uuid, name, start, end, fn))
  response.setJSON()
  response.append(json.dumps([responseString]))
  return

def job(rfam, response):
  # Extract the request - path plus parameters...
  path  = response.getPath()[2:]
  name = response.getQuery()['name']
  start = int(response.getQuery()['start'])
  end   = int(response.getQuery()['end'])
  final = response.getQuery()['final']=='true'
  
  # Verify the path exists...
  db = rfam.proj(response.project)
  if path not in db:
    response.setJSON()
    response.append('false')
  
  # Convert path into a proper filename...
  ps = rfam.getProject(response.project)
  fn = os.path.join(ps['directory'], *path)
  
  # Calculate the jobs default priority...
  json_path = path[:]
  json_path[-1] += '.json'
  
  if json_path in db:
    priority = true_priority(rfam, response.project, db[json_path], db)
  else:
    settings = rfam.proj_defaults(response.project)['priority.json'].read()
    priority = settings['low']
  
  # Create the job...
  uuid = rfam.jobs.add(name, response.project, fn, start, end, priority, final, [], json_path)
  
  # Return success...
  rfam.log(response, 'new_job(%s,%s,%i,%i,%s)' % (uuid, name, start, end, fn))
  response.setJSON()
  response.append('true')



def role(rfam, response):
  response.setJSON()
  
  # Extract the details...
  if 'role' not in response.getQuery():
    response.make418()
    return
    
  if 'user' not in response.getQuery():
    response.make418()
    return
  
  role = saxutils.unescape(response.getQuery()['role'])
  user = response.getQuery()['user']
  ident = str(uuid.uuid4())
  
  # Verify that the user is sane...
  if user not in rfam.getUsersByProject(response.project):
    response.append('false')
    return
  
  # Create the new role entry...
  proj = rfam.proj(response.project)['project.json']
  p = proj.read()
  if len(p['roles'])>0:
    order = max(map(lambda d: d['order'], p['roles'].values())) + 1.0
  else:
    order = 0
  p['roles'][ident] = {'role' : role, 'user' : user, 'order' : order}
  proj.write(p)
    
  # Report success...
  rfam.log(response, 'new_role(%s,%s)' % (role, user))
  response.append('true')

  
  
def ext_asset(rfam, response):
  response.setJSON()
  
  # Extract the details...
  if 'description' not in response.getQuery():
    response.make418()
    return
    
  if 'license' not in response.getQuery():
    response.make418()
    return

  if 'origin' not in response.getQuery():
    response.make418()
    return

  description = saxutils.unescape(response.getQuery()['description'])
  license     = saxutils.unescape(response.getQuery()['license'])
  origin      = saxutils.unescape(response.getQuery()['origin'])
  ident       = str(uuid.uuid4())
  
  # Create the new entry...
  proj = rfam.proj(response.project)['project.json']
  p = proj.read()
  p['ext_assets'][ident] = {'description' : description, 'license' : license, 'origin' : origin}
  proj.write(p)
  
  # Report success...
  rfam.log(response, 'new_external_asset(%s,%s,%s,%s)' % (ident, description, license, origin))
  response.append('true')
  response.add()



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
  elif path[1]=='job_prman':
    job_prman(rfam, response)
  elif path[1]=='role':
    role(rfam, response)
  elif path[1]=='ext_asset':
    ext_asset(rfam, response)
  else:
    response.make418()
