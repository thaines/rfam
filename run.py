#! /usr/bin/env python3
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
import wsgiref.simple_server

import urllib3.connection

from main import application



# Load the configuration...
f = open('config.json', 'r')
config = json.loads(f.read())
f.close()



# Run a slightly tweaked wsgi server...
class BetterWSGIServer(wsgiref.simple_server.WSGIServer):
  request_queue_size = 1024*32 # Increases the backlog, so it can handle more concurrent connections! Bit insane, but meh.
  request_timeout = 8

  def get_request(self):
    request, client_addr = super().get_request()
    request.settimeout(self.request_timeout)
    return request, client_addr


server = BetterWSGIServer(('', config['port']), wsgiref.simple_server.WSGIRequestHandler)
server.set_app(application)
server.serve_forever()
