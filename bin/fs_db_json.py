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

from .fs_db import FileType



class JsonFileType(FileType):
  """Allows the FSDB system to access json file via the standard Python json reader/writer. Returns None on getting a dud file - user has to decide what to do with that."""
  def extension(self):
    return '.json'
  
  def read(self, f):
    try:
      return json.load(f)
    except ValueError:
      return None
  
  def write(self, f, data):
    json.dump(data, f)
