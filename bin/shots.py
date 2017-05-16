# Copyright 2017 Tom SF Haines

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



def attr_escape(s):
  return saxutils.escape(s).replace('"',"&quot;")



def app(rfam, response):
  # If the user is not logged in show them the login page...
  if response.user==None or response.project==None:
    login(rfam, response)
    return
  
  # Generate the list of shots for the table...
  shots = []
  
  db = rfam.proj(response.project)
  old = rfam.getLanguage(response.user)['old']
  
  ident = 0
  for path in db:
    if old in path: continue # Skip depreciated versions of files.
    node = db[path]
    if node.isa()==node.FILE and path[-1].endswith('.json'):
      meta = node.read()
      if meta==None or ('type' not in meta) or ('owner' not in meta):
        continue
      if not meta['render']:
        continue
      
      owner = rfam.userChoice(response.project, meta['owner'], True)
      rating = int(meta['rating']) if 'rating' in meta else 0
      
      payload = {'id' : str(ident), 'path' : attr_escape(('/'.join(path))[:-5]), 'name' : meta['name'], 'owner' : owner, 'r1' : 'on' if rating>=1 else 'off', 'r2' : 'on' if rating>=2 else 'off', 'r3' : 'on' if rating>=3 else 'off', 'r4' : 'on' if rating>=4 else 'off', 'r5' : 'on' if rating>=5 else 'off'}
      shots.append((meta['name'], rfam.template('shots.row', payload, response)))
      
      ident += 1
  
  shots.sort()
  shots = '\n'.join([shot[1] for shot in shots])
  
  # Show the shots page...
  head = '<link rel="stylesheet" href="/stylesheets/shots.css"/>\n<script src="/javascript/shots.js"></script>'
  payload = {'title' : rfam.getLanguage(response.user)['shots'], 'head' : head, 'shots' : shots}

  html = rfam.template('shots', payload, response)
  response.append(html)
  response.setHTML()
