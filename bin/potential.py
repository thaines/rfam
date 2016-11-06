# Copyright 2015 Tom SF Haines

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



def app(rfam, response):
  # We are expecting a post of json, containing just a string - get and verify...
  request = response.getJsonPost()
  
  if not isinstance(request, str):
    response.make418()
    return
  
  
  # Feed name into job system to get a list of jobs to return...
  jobs = rfam.jobs.potential_jobs(request)
  
  
  # Reformat job list to required format...
  ret = []
  
  for job in jobs:
    frames = len(job['todo']) + len(job['working']) + len(job['done'])
    
    tweaked = {'uuid' : job['uuid'], 'name' : job['name'], 'created' : job['created'], 'file' : job['file'], 'priority' : job['priority'], 'video' : job['video'], 'requires' : job['requires'], 'frames' : frames}
    
    ret.append(tweaked)
  
  
  # Return newly formated job list as json...
  response.setJSON()
  response.append(json.dumps(ret))
