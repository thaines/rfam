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



def app(rfam, response):
  # If the user is not logged in show them the login page...
  if response.user==None or response.project==None:
    login(rfam, response)
    return
  
  # Figure out the list of asset types...
  choice_type = rfam.typeChoice(response.project)
  
  # Show the new asset page...
  head = '<link rel="stylesheet" href="/stylesheets/new.css"/>\n<script src="/javascript/new.js"></script>'
  payload = {'title' : rfam.getLanguage(response.user)['new_asset'], 'head' : head, 'choice_type' : choice_type}
  html = rfam.template('new', payload, response)
  response.append(html)
  response.setHTML()
