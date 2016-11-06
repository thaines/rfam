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


cache = dict()



def app(rfam, response):
  name = response.getPath()[-1]
  
  if name not in cache:
    path = rfam.getStylesheetsPath()
    fn = os.path.join(path, name)
    
    f = open(fn)
    cache[name] = f.read()
    f.close()
  
  response.setCSS()
  if not rfam.development():
    response.allowCache()
  response.append(cache[name])
