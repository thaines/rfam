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
import json
import xml.sax.saxutils as saxutils



def app(rfam, response):
  # Verify the user is logged in...
  if response.user==None or response.project==None:
    response.make403()
    return
  
  response.setJSON()
  
  # Figure out the .json file for the requested node, if it doesn't exist return default information...
  path = response.getPath()[1:]
  name = path[-1]
  path[-1] += '.json'
  
  db = rfam.proj(response.project)
  if path not in db:
    response.append(json.dumps({'name' : name, 'start' : 1, 'end' : 24, 'final' : False}))
    return
  
  info = db[path].read()
  
  # Augment the information with extra stuff extracted from the .blend file...
  info = dict(info)
  info['start' ] = 1 # Need to extract these from the file!
  info['end' ] = 24
  
  # Return the contents of the .json file...
  response.append(json.dumps(info))
