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

from bin.rfam import RFAM
from bin.response import Response



# Create the RFAM object...
rfam = RFAM()



# Initialise the list of modules for handling requests...
from bin import javascript # Provides javascript files
from bin import stylesheets # Provides stylesheet files
from bin import logo # Provides the logo image!
from bin import icon # Provides the icon image!
from bin import head # Provides the image of a user.
from bin import heads # Provides the image of a team.
from bin import images # Provides access to the various images - the update status icons for ajax.

from bin import login # The login screen.
from bin import home # The home screen, which shows a summary of current users tasks.
from bin import assets # Asset list screen.
from bin import asset # Screen for editing a single asset.
from bin import new # Screen for creating a new asset.
from bin import team #  Screen that shows the team and what they should be working on.
from bin import project # Screen that shows the project overview.
from bin import shots # Overview of shots and their state.
from bin import rendering # Web interface for rendering.

from bin import store # Handles all the ajax updates for all the interface elements.
from bin import add # Ajax code for adding assets, render jobs, rolls in the credits and external assets,
from bin import remove # Opposite to above.
from bin import action # Bunch of random ajax things, such as making a file checkpoint.

from bin import selector # Provides the file selector used on the rendering screen.
from bin import info # gets information about a file as part of above.

from bin import farm # The interface to the render farm used by render nodes.
from bin import potential # The interface used by the pre-node, for rendering on a cluster.

from bin import credits # Provides the automatically generated credit roll.


modules = dict()
modules['javascript'] = javascript.app
modules['stylesheets'] = stylesheets.app
modules['logo'] = logo.app
modules['icon'] = icon.app
modules['head'] = head.app
modules['heads'] = heads.app
modules['images'] = images.app

modules['login'] = login.app
modules['home'] = home.app
modules['assets'] = assets.app
modules['asset'] = asset.app
modules['new'] = new.app
modules['team'] = team.app
modules['project'] = project.app
modules['shots'] = shots.app
modules['rendering'] = rendering.app

modules['store'] = store.app
modules['add'] = add.app
modules['remove'] = remove.app
modules['action'] = action.app

modules['selector'] = selector.app
modules['info'] = info.app

modules['farm'] = farm.app
modules['potential'] = potential.app

modules['credits'] = credits.app

modules[''] = home.app



# The actual application that responds to everything...
def application(environ, start_response):
  response = Response(environ)
  cookie = response.getCookie()

  # Check if the user is logged in, and record this fact in the response...
  response.project = None
  response.project_name = '<<Unknown>>'
  if 'project' in cookie:
    project = rfam.getProject(cookie['project'])
    if project!=None:
      response.project = cookie['project']
      response.project_name = project['name']

  response.user = None
  response.user_name = '<<Unknown>>' 
  if 'user' in cookie:
    user = rfam.getUser(cookie['user'])
    if user!=None:
      response.user = cookie['user']
      response.user_name = user['name']
  
  # Process the url properly - start by extracting the path...
  path = response.getPath()
  base = path[0] if len(path)!=0 else ''
  
  # Find the relevant module to provide the return data, or 404 if none found...
  if base in modules:
    modules[base](rfam, response)
  else:
    response.make404()
  
  # Return the actual data...
  return response.response(start_response)
