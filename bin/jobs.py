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

import os
import os.path
import time

import random
import math
import uuid
from collections import defaultdict

from .fs_db import FSDB
from .fs_db_json import JsonFileType



def bin_search_order(items):
  """Given a list this reorders it into 'binary search order' (breadth first), on the principal that if your checking every entry and errors have ordering coherance this puts it into a good order in which to do the calculation, to maximise the chance of bumping into errors early. Returns the reordered list"""
  stack = [(1,len(items)-1)]
  ret = [items[0], items[len(items)-1]]
  
  while len(stack)!=0:
    low, high = stack.pop(0)
    
    if (high-low)<4:
      for i in range(low, high):
        ret.append(items[i])
    
    else:
      half = (high-low) // 2 + low
      ret.append(items[half])
      
      stack.append((low, half))
      stack.append((half+1, high))
  
  return ret

  

class Jobs:
  """Basically the state of the render farm - all cached to the directory specified by the key 'jobs' in the main configuration file. Jobs are represented by dictionaries, of the form: {'uuid' : Unique identifier, used with nodes, 'name' : A name for the job, used with fleshies - defaults to the name of the asset being rendered, but user customisable, 'file' : File to render, starting with a path identifier so its computer agnostic, 'path' : The path identifier seperate from file, so it can be quickly checked for compatiblity with a select request, 'priority' : Priority, as an integer multiplier; same as asset priorities, 'project' : The project it is associated with, for display, balancing and edit permissions, 'video' : If True render a video, i.e. send it to a single node for the entire frame range, 'requires' : List of node features it requires, as short strings, 'pause' : True if its not being done right now, 'todo' : List of frames to render; for video mode it just uses the minimum and maximum, 'working' : List of jobs that are currently running, as list [frame #, node identifier, last confirmation (time since epoch)]; frame # will be (min, max) for a video render, 'done' : List of frames that have been done, noting that for video rendering this updates as a job is run, 'time' : Average time to render a frame thus far, so long render times don't dominate the farm over short render times, 'time_count' : Number of values that have gone into the render time thus far; when zero rendering a frame takes top priority, so the system always tries to render a single frame from a job as quickly as possible so breakage can be discovered quickly, 'errors' : Number of errors that have been returned whilst trying to render; after a threshold rendering stops}"""
  
  def __init__(self, rfam):
    """Given the rfam object, so it can get at the projects etc."""
    self.rfam = rfam
    self.retry = self.rfam.config['retry']
    
    # Prepare the jobs directory -  a .json file for each job, accessed via a FSDB...
    if not os.path.exists(self.rfam.config['jobs']):
      os.makedirs(self.rfam.config['jobs'])
        
    self.jobs = FSDB(self.rfam.config['jobs'], rfam.config['single_proc'])
    self.jobs.register(JsonFileType())
    
    # Prepare the nodes directory - a .json directory for each known node, accessed via a FSDB...
    if not os.path.exists(self.rfam.config['nodes']):
      os.makedirs(self.rfam.config['nodes'])
        
    self.nodes = FSDB(self.rfam.config['nodes'], rfam.config['single_proc'])
    self.nodes.register(JsonFileType())
    
    # Extract a few misc parameters...
    self.bin_search_order = self.rfam.config['bin_search_order']
    
    # The system for estimating what percentage of nodes have the given features, so it can fairly handle deployment of jobs which require those features...
    self.require_rate = dict() # Dictionary of rates by 
    self.require_init = 1.0 # Probability of something previously unseen.
    self.require_shrink = math.pow(0.5, 1.0 / self.rfam.config['require_half_life']) # Number of jobs for stat to reach half strength.
    self.require_add = 1.0 - self.require_shrink
    
    # Time information, for job updates etc...
    self.heartbeat = self.rfam.config['heartbeat'] # How often clients should say hi.
    self.timeout = self.rfam.config['heartbeat'] * self.rfam.config['timeout_scale'] # If a client hasn't said hi this long the task is sent to another node.
    
    # Stuff for time estimation of jobs...
    self.min_render_time = self.rfam.config['min_render_time']
    self.unknown_render_time = self.rfam.config['unknown_render_time']
    
  
  def iterjobs(self):
    """An iterator over the jobs in the system. Each job is represented as defined by the class description, so this outputs large dictionaries."""
    root = self.jobs.get_root()
    for name, node in [(name, root[name]) for name in root]:
      if node.isa()==node.FILE and name.endswith('.json'):
        ret = node.read()
        if ret!=None:
          yield ret
  
  
  def iternodes(self):
    """Iterates over the known nodes in the system, returning a dictionary for each, containing {'ident' : Its identifier, 'provides' : A list of strings indicating stuff the node provides, 'paused' : True if its paused, 'seen' : seconds since epoc it was last seen.}"""
    root = self.nodes.get_root()
    if self.rfam.config['show_overdue']:
      too_old = time.time() - self.rfam.config['timeout_node']
    else:
      too_old = time.time() - self.timeout
    
    to_die = []
    
    for name in root:
      node = root[name]
      if node.isa()==node.FILE and name.endswith('.json'):
        ret = node.read()
        if ret!=None:
          if ret['seen'] > too_old:
            yield ret
            
          else:
            to_die.append(node)
    
    for node in to_die:
      node.remove()
  
  
  def add(self, name, project, fn, min_frame, max_frame, priority, video = False, requires = [], meta = None):
    """Adds a job - takes quite a lot of parameters but initialises a bunch more. Returns the uuid of the new job. name is a human readable identifier, project the identifier of the project its from, fn the filename, including a path, so its filesystem agnostic, min_frame and max_frame define the range to render, priority the priority of rendering. video can be set to True to use video mode and requires is a list of strings, identifying features that rendering nodes must have to render this asset."""
    
    job = dict()
    job['uuid'] = uuid.uuid1().hex
    job['name'] = name
    job['created'] = time.time()
    job['file'] = fn
    job['path'], _ = fn.split('::', 1)
    job['priority'] = priority
    job['project'] = project
    job['meta'] = meta
    job['video'] = video
    job['requires'] = tuple(requires)
    job['pause'] = False
    job['todo'] = list(range(min_frame, max_frame+1))
    job['working'] = []
    job['done'] = []
    job['failed'] = []
    job['time'] = 0.0
    job['time_count'] = 0
    job['errors'] = 0
    job['potential'] = [] # For the potential jobs system.
    
    if self.bin_search_order:
      job['todo'] = bin_search_order(job['todo'])
    
    self.jobs.get_root().new(job['uuid'] + '.json', job)
    
    return job['uuid']
  
  
  def exists(self, uuid):
    """Given the uuid of a job this returns True if it exists, False if not."""
    return (uuid+'.json') in self.jobs.get_root()

    
  def remove(self, uuid):
    """Given the uuid of a job this attempts to terminate it."""
    self.jobs.get_root()[uuid+'.json'].remove()
    
    
  def node_exists(self, uuid):
    """Given the uuid of a node this returns True if it exists, False if not."""
    return (uuid+'.json') in self.nodes.get_root()
  

  def job_pause(self, ident, value = True):
    """Allows you to pause or unpause a job, depending on if you hand in True or False to value, respectivly."""
    root = self.jobs.get_root()
    fn = ident + '.json'
    if fn not in root:
      return
    
    node = root[fn]
    state = node.read()
    state['pause'] = value
    node.write(state)


  def job_priority(self, ident, value):
    """Sets the priority of a job."""
    root = self.jobs.get_root()
    fn = ident + '.json'
    if fn not in root:
      return
      
    node = root[fn]
    state = node.read()
    state['priority'] = value
    node.write(state)

    
  def node_pause(self, ident, value = True):
    """Allows you to pause or unpause a node, depending on if you hand in True or False to value, respectivly."""
    root = self.nodes.get_root()
    fn = ident + '.json'
    if fn not in root:
      return
    
    node = root[fn]
    state = node.read()
    state['paused'] = value
    node.write(state)


  def node_pause_all(self, value):
    root = self.nodes.get_root()
    
    for name in root:
      node = root[name]
      
      state = node.read()
      if state!=None:
        state['paused'] = value
        node.write(state)


  def report(self, ident, provides = [], version = None):
    """Called when a job checks in - allows the system to maintain a list of active nodes. Also allows it to keep stats on what nodes typically provide."""
    
    # Record this nodes sighting...
    root = self.nodes.get_root()
    fn = ident + '.json'
    if fn in root:
      state = root[fn].read()
    else:
      state = None

    if state==None:
      state = {'ident' : ident, 'paused' : False}
    
    state['provides'] = provides
    state['version'] = version
    state['seen'] = time.time()
    
    root.new(fn, state)
    
    # Analyse the provides variable - we need to keep rolling stats on how many nodes are arriving of each type so that it can correctly upweight jobs with essoteric requirements so they get done in a fair amount of time (for practical reasons assume items in the provides list are independent - if jobs only ever have one requires this is correct anyway)...
    self.require_init *= self.require_shrink
    for key in self.require_rate.keys():
      self.require_rate[key] *= self.require_shrink

    for key in provides:
      if key not in self.require_rate:
        self.require_rate[key] = self.require_init
      self.require_rate[key] += self.require_add


  def task_select(self, ident, paths, provides = []):
    """Selects a job - you provide a list of paths the node has access to and a list of strings for features that it provides. From this it selects and returns a job, noting that it will record that the node with the given ident is working on it. If no job is avaliable it returns None; if one is avaliable it returns the dictionary {'uuid' : uuid of job, 'frame' : index of frame to render, min-max tuple to do a video render, 'file' : File of the .blend to render, inc. path, 'issued' : GMT time of issue, 'requires' : List of features it requires.}. Node that this assumes that the user called report for the given ident first."""

    # Loop all jobs, calculating the weight (factor in priority, runtime and requires!) of selecting a work item from each, where compatible...
    options = defaultdict(list)
    now = time.time()
    too_old = now - self.timeout
    
    for name in self.jobs.get_root():
      # Convert into json dictionary...
      job = self.jobs[name].read()
      if job==None:
        continue
      
      # Ignore paused jobs...
      if job['pause']==True:
        continue
      
      # Check that the job is compatible with this node...
      if job['path'] not in paths:
        continue

      not_comp = False
      for req in job['requires']:
        if req not in provides:
          not_comp = True
          break
      if not_comp:
        continue
      
      # Now verify the job has undone work - includes checking for timed out working entries if necesary...
      if len(job['todo'])==0:
        no_work = True
        if self.retry:
          for task in job['working']:
            if task[2] < too_old:
              no_work = False
              break
        if no_work:
          continue
      
      # Calculate the jobs weight...
      weight = max(job['priority'], 1e-3)
      for req in job['requires']:
        weight /= self.require_rate[key]
      if job['time_count']!=0:
        weight /= max(job['time'], self.min_render_time) / self.min_render_time
      elif len(job['working'])==0:
        weight *= 1024.0 # First frame renders are heavily prioritised.
      else:
        weight /= self.unknown_render_time
      
      # Store the job in a project specific queue, so we can first draw a project to keep that fair...
      options[job['project']].append((weight, job))
      
    # Draw a job (project then job), select which work item we are going with...
    ## Project...
    if len(options)==0:
      return None # No work!
    
    elif len(options)==1:
      option = next(iter(options))
      
    else:
      total = 0.0
      weight = dict()
      
      for key in options.keys():
        # For fairness bias so each project has roughly the same number of nodes, in the ratio of the project priorities...
        nodes = sum([len(job['working']) for weight, job in options[key]])
        w = self.rfam.getProject(key)['render.priority'] / (0.1 + nodes)
        
        weight[key] = w
        total += weight[key]
      
      r = random.random() * total
      
      for key in options.keys():
        r -= weight[key]
        if r<=0.0:
          option = key
          break

    ## Job...
    total = 0.0
    for weight, job in options[option]:
      total += weight
    
    r = random.random() * total
    
    for weight, job in options[option]:
      r -= weight
      if r<=0.0:
        todo = job
        break
    
    # Record the work item and return (re-get it to minimise the risk of corruption - should probably change how this system works)...
    root = self.jobs.get_root()
    name = todo['uuid'] + '.json'
    todo = root[name].read()
    
    inc_error = 0
    ok = False
    
    if len(todo['todo'])!=0:
      ok = True
      if todo['video']:
        frame = (min(todo['todo']), max(todo['todo']))
        todo['todo'] = []
      else:
        frame = todo['todo'].pop(0)
    
    elif self.retry:
      for i in range(len(todo['working'])):
        if todo['working'][i][2] < too_old:
          inc_error = 1
          ok = True
          frame = todo['working'][i][0]
          del todo['working'][i]
          if todo['video']:
            todo['done'] = []
          break
    
    if not ok: # Something has gone wrong - avoid a crash.
      return None
      
    task = [frame, ident, now]
    todo['working'].append(task)
    todo['errors'] += inc_error
    
    root[name].write(todo)
    
    # Return the task for the node to do...
    return {'uuid' : todo['uuid'], 'frame' : task[0], 'file' : todo['file'], 'issued' : now, 'requires' : todo['requires']}
  
  
  def task_alive(self, ident, uuid, frame, done = 0, total = 1):
    """Called to indicate that we just received a heartbeat for the given task, so it can be kept alive. ident is provided so that it can verify the node should be doing the task - returns True if it should continue, False if it should die."""
    
    # Get the node data...
    root = self.jobs.get_root()
    name = uuid + '.json'
    if name not in root:
      return False
    
    node = root[name].read()
    
    # Perform the update - depends on if its video mode or individual frame mode...
    if node['video']==False:
      # Single frame...
      found = False
      for task in node['working']:
        if task[0]==frame:
          if task[1]==ident:
            task[2] = time.time()
          else:
            # Another node is rendering it - hard stop...
            return False
          
          found = True
          break
      
      if not found:
        # Node is not meant to be rendering the asset, but then no one else is - might as well let it continue...
        node['working'].append([frame, ident, time.time()])
    
    else:
      # Video mode...
      if len(node['working'])==0:
        # Job doesn't exist - might as well assign it to the node...
        node['todo'] = []
        node['working'] = [[frame, ident, time.time()]]
      
      else:
        # Job exists - check its the right node...
        if node['working'][0][1]!=ident:
          return False
        
        node['working'][0][2] = time.time()
      
      # Update for the done/total values...
      node['done'] = [i+frame[0] for i in range(done)]
    
    # Save the node back...
    root[name].write(node)
    
    # We got this far - there were no problems...
    return True
  
  
  def task_done(self, uuid, frame, time):
    """Called to indicate that a task has been completed."""
    
    # Get the node data...
    root = self.jobs.get_root()
    name = uuid + '.json'
    if name not in root:
      return False
    
    node = root[name].read()
    
    # Mark the task as complete, noting that code depends on if its a video render or not...
    if node['video']==False:
      # Single frame...
      for i in range(len(node['working'])):
        if node['working'][i][0]==frame:
          # Update data structure...
          del node['working'][i]
          node['done'].append(frame)
          
          # Update rendering time information for the job...
          node['time_count'] += 1
          node['time'] += (time - node['time']) / float(node['time_count'])
          
          # Update file timing information, if relevant...
          db = self.rfam.proj(node['project'])
          if node['meta'] in db:
            meta_node = db[node['meta']]
            meta = meta_node.read()
            
            if 'render_time' not in meta:
              d = {}
              meta['render_time'] = d
            else:
              d = meta['render_time']
            
            if str(frame) not in d:
              d[str(frame)] = [time]
            else:
              d[str(frame)].append(time)
            
            meta_node.write(meta)
          
          break
    
    else:
      # Video mode...
      
      # Update data structure...
      node['todo'] = []
      node['working'] = []
      node['done'] = [i for i in range(frame[0], frame[1]+1)]
      
      # Update rendering time information, even though pointless...
      node['time_count'] += 1
      node['time'] += (time - node['time']) / float(node['time_count'])
      
      # Update file timing information, if relevant...
      db = self.rfam.proj(node['project'])
      if node['meta'] in db:
        meta_node = db[node['meta']]
        meta = meta_node.read()
            
        if 'render_time' not in meta:
          d = {}
          meta['render_time'] = d
        else:
          d = meta['render_time']
            
        if 'video' not in d:
          d['video'] = [time]
        else:
          d['video'].append(time)
            
        meta_node.write(meta)
    
    # Save the node back...
    root[name].write(node)
  
  
  def potential_jobs(self, task):
    """Returns a list of all jobs that have not been tagged with the given name, tagging them with that name such that they will not be returned next time the method is called (with the same name). Each job is represented by a dictionary, containing all of the relevant information."""
    root = self.jobs.get_root()
    ret = []
    
    
    for name, node in [(name, root[name]) for name in root]:
      if node.isa()==node.FILE and name.endswith('.json'):
        state = node.read()
        if state!=None and task not in state['potential']:
          state['potential'].append(task)
          node.write(state)
        
          ret.append(state)
    
    return ret
