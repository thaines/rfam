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



def app(rfam, response):
  # Get the path and check its a valid request for a head...
  path = response.getPath()
  if len(path)!=2:
    response.make404()
    return
  
  # Find the relevant user record...
  user = rfam.getUser(path[1])
  if user==None:
    response.make404()
    return
  
  path = rfam.real(user['image'])
  
  if path[-4:]=='.png':
    response.setPNG()
  else:
    response.setJPEG()

  response.allowCache()
  
  response.provideFile(open(path, 'rb'))
