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



def format_bytes(bytes):
  """Given a number of bytes this returns a human readable representation as a string."""
  options = [(1024*1024*1024*1024, 'TiB'), (1024*1024*1024, 'GiB'), (1024*1024, 'MiB'), (1024, 'KiB')]
  
  for size, postfix in options:
    if bytes>=size:
      return '%.2f %s' % (float(bytes) / float(size), postfix)
  
  return '%i b' % bytes
