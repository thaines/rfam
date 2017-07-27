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

import time
import os

try:
  import fcntl
except:
  fcntl = None # If this happens then 'video' rendering mode is disabled.

import subprocess
if not hasattr(subprocess, 'DEVNULL'):
  subprocess.DEVNULL = open(os.devnull, 'w')



class Worker:
  """Simple entity for managing a seperate process that is running a render in Blender - simple wrapper that handles all the tedious Blender-specific stuff."""
  def __init__(self, node, threads = 1):
    """Provided with the Node object and the number of threads to pass through to Blender each time it is run."""
    self.node = node
    self.threads = threads
    
    # Process into which its running something, None if nothing has been run...
    self.proc = None
    
    # Other state...
    self.uuid = None
    self.fn = None
    self.frame = None
    self.start = time.time()
    self.video = False
    self.last_line = ''
  
  
  def busy(self):
    """Returns True if the worker has work, False if it does not."""
    return not (self.proc==None or self.proc.poll()!=None)
  
  def p(self):
    """Returns the process, or None if its not running, so it can wait for something to happen."""
    if self.proc!=None and self.proc.poll()==None:
      return self.proc
    else:
      return None
  
  
  def state(self):
    """Either returns the state of the node or None, if there is no state to return. Note that when a task completes it may not be busy but it still has to return that it completed the job."""
    if self.proc==None:
      return None
    
    poll = self.proc.poll()
    if poll==None:
      # Still running...
      done = 0
      total = 1
      
      # Handle video mode - ugh...
      if self.video:
        total = self.frame[1] + 1 - self.frame[0]
        
        # Ok, we have access to stdout - get data, find most recent output line and analyse...
        try:
          self.last_line += self.proc.stdout.read()
        except TypeError: # Seems to randomly occur - not sure why, but its a node killer.
          pass
        parts = self.last_line.split('\n')
        if len(parts)>1:
          self.last_line = parts[-2] + '\n' + parts[-1]
        
        first = parts[-2].split(' ')[0]
        if first.startswith('Fra:'):
          done = int(first[4:]) - self.frame[0]
      
      return {'id' : 'report', 'uuid' : self.uuid, 'frame' : self.frame, 'done' : done, 'total' : total}
    elif poll==0:
      # Finished running and has not told server this fact...
      self.proc = None # Remove the process - the server now knows its done.
      now = time.time() # Some potential inaccuracy here, but no easy solution
      return {'id' : 'done', 'uuid' : self.uuid, 'frame' : self.frame, 'time' : now - self.start}
    else:
      # Something has gone wrong - give up...
      return None


  def run(self, commandment):
    """Only call if busy is False - sets a job running and state has been called. commandment must be a dictionary returned by the server with an id of task."""
    if (not isinstance(commandment['frame'], int)) and (fcntl is None):
      return # Drop video commandments - server isn't going to like this, but meh.
    
    self.uuid = commandment['uuid']
    self.frame = commandment['frame']
    
    self.fn = self.node.to_local(commandment['file'])
    
    if isinstance(self.frame, int):
      start = self.frame
      end = self.frame
      self.video = False
    else:
      start = self.frame[0]
      end = self.frame[1]
      self.video = True
    
    if 'scripting' not in self.node.config or self.node.config['scripting']:
      script = '-y'
    else:
      script = '-Y'
    
    if 'blender_env' in self.node.config and len(self.node.config['blender_env'])>0:
      env = os.environ.copy()
      for key, value in self.node.config['blender_env'].items():
        env[key] = value
      
    else:
      env = None
    
    self.proc = subprocess.Popen(['nice', '-n', str(self.node.config['nice']), self.node.blender, '-t', str(self.threads), script, '-b', self.fn, '-s', str(start), '-e', str(end), '-a'], stdout = subprocess.PIPE if self.video else subprocess.DEVNULL, stderr = subprocess.DEVNULL, env=env, universal_newlines=True)
    self.start = time.time()
    
    if self.video:
      self.last_line = ''
      fd = self.proc.stdout.fileno()
      fl = fcntl.fcntl(fd, fcntl.F_GETFL)
      fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)


  def kill(self, commandment):
    """Given a commandment with an id of kill it does it, but only if the details match."""
    if self.proc!=None and commandment['uuid']==self.uuid and commandment['frame']==self.frame:
      self.proc.kill()
      self.proc.wait()
      self.proc = None
  
  def kill_all(self):
    """For when you just want it all dead."""
    if self.proc!=None:
      self.proc.kill()
      self.proc.wait()
      self.proc = None
