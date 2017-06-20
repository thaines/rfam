#! /usr/bin/env python3
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

import sys
import os.path
import json
import csv



# Takes a csv file of <name>, <internal name>, <project>, .. as many projects as you want and generates accounts in the user directory. Ignores any account that already exists and queries config.json to make sure it's doing the right thing. Note that it assumes images go in a path that starts 'images:'...

language = "english"



# Check we have a filename...
if len(sys.argv)<2:
  print('Usage: ./csv_to_users.py <csv file>')
  sys.exit(1)



# Load the configuration...
f = open('config.json', 'r')
config = json.loads(f.read())
f.close()



# Load the csv file, and loop each line in turn...
for row in csv.reader(open(sys.argv[1], newline='')):
  name = row[0].strip()
  username = row[1].strip()
  projects = [n.strip() for n in row[2:] if len(n)!=0]
  
  
  fn = os.path.join(config['users'], username + '.json')
  if not os.path.exists(fn):
    print('Adding:')
    print('  name = %s' % name)
    print('  username = %s' % username)
    print('  projects = %s' % str(projects))
    
    f = open(fn, 'w')
    json.dump({'ident' : username, "name" : name, "image" : "images::%s.jpg"%username, "projects" : projects, "language" : language}, f, indent=1)
    f.close()
  
  else:
    print('%s already exists - skipping' % username)
